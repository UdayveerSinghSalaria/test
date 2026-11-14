"""Gmail API service: real users.messages calls against the user's mailbox.

Responsibilities:
  * list latest N messages (with pageToken pagination)
  * fetch a single message with full payload
  * decode multipart/alternative & multipart/* bodies (base64url, quoted-printable)
  * sanitize any HTML before it can reach a browser (never render raw)
  * map Gmail API failures to actionable errors

Email bodies are NEVER written to logs or the activity audit log.
"""

from __future__ import annotations

import base64
import logging
import re
from datetime import datetime, timezone
from email.message import EmailMessage
from email.header import decode_header, make_header
from html import unescape
from html.parser import HTMLParser

import httpx

from ..schemas import EmailAddress, EmailDetail, EmailSummary

logger = logging.getLogger(__name__)

GMAIL_BASE = "https://gmail.googleapis.com/gmail/v1/users/me"
LIST_FIELDS = "messages(id,threadId,snippet),nextPageToken"
MESSAGE_FIELDS = "id,threadId,labelIds,payload,snippet,internalDate,sizeEstimate"


class GmailError(Exception):
    """Actionable Gmail failure (auth revoked, quota, network...)."""


# ---------------------------------------------------------------------------
# HTML sanitization
# ---------------------------------------------------------------------------
ALLOWED_TAGS = {
    "p", "br", "b", "strong", "i", "em", "u", "s", "ul", "ol", "li",
    "blockquote", "code", "pre", "a", "h1", "h2", "h3", "h4", "h5", "h6",
    "div", "span", "hr", "table", "thead", "tbody", "tr", "td", "th",
    "caption", "figure", "img", "sub", "sup",
}
ALLOWED_ATTRS = {"a": {"href", "title"}, "img": {"src", "alt", "width", "height"}}
_URL_SCHEME_OK = re.compile(r"^(https?:|mailto:|#)", re.IGNORECASE)


class _Sanitizer(HTMLParser):
    """Allowlist sanitizer: keeps safe tags/attrs, drops scripts/styles/events."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.out: list[str] = []
        self._skip_depth = 0  # inside <script>/<style>/<iframe>...

    def handle_starttag(self, tag: str, attrs) -> None:
        tag = tag.lower()
        if tag in {"script", "style", "iframe", "object", "embed", "noscript", "template", "svg"}:
            self._skip_depth += 1
            return
        if self._skip_depth or tag not in ALLOWED_TAGS:
            return
        kept = []
        for k, v in attrs:
            k = k.lower()
            if k.startswith("on") or k in {"style", "class", "id"}:
                continue
            if k in {"href", "src"}:
                v = (v or "").strip()
                if not _URL_SCHEME_OK.match(v):
                    continue  # javascript:, data:, vbscript: -> drop attr
                if k == "href":
                    v = unescape(v)
            elif k not in ALLOWED_ATTRS.get(tag, set()):
                continue
            kept.append(f'{k}="{re.sub(chr(34), "&quot;", str(v))}"')
        suffix = " " + " ".join(kept) if kept else ""
        if tag == "br":
            self.out.append("<br/>")
        else:
            self.out.append(f"<{tag}{suffix}>")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in {"script", "style", "iframe", "object", "embed", "noscript", "template", "svg"}:
            self._skip_depth = max(0, self._skip_depth - 1)
            return
        if self._skip_depth or tag not in ALLOWED_TAGS or tag == "br":
            return
        self.out.append(f"</{tag}>")

    def handle_data(self, data: str) -> None:
        if not self._skip_depth:
            self.out.append(escape_text(data))


def escape_text(data: str) -> str:
    return data.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def sanitize_html(html: str) -> str:
    """Return HTML safe to embed in the app. Scripts/events/URLs filtered."""
    s = _Sanitizer()
    try:
        s.feed(html)
        s.close()
    except Exception:  # malformed HTML: fall back to escaped text
        logger.debug("HTML sanitizer hit malformed input; escaping instead")
        return escape_text(re.sub(r"<[^>]+>", " ", html))
    return "".join(s.out)


# ---------------------------------------------------------------------------
# Header / body decoding helpers
# ---------------------------------------------------------------------------
def decode_mime_header(value: str | None) -> str:
    """Decode RFC 2047 encoded-words (=?utf-8?B?...?=) in a header."""
    if not value:
        return ""
    try:
        return str(make_header(decode_header(value)))
    except Exception:
        return value


def _b64url_decode(data: str) -> bytes:
    pad = -len(data) % 4
    return base64.urlsafe_b64decode(data + "=" * pad)


def _parse_address(raw: str) -> EmailAddress:
    """'Jane Doe <jane@x.com>' -> EmailAddress(name='Jane Doe', address='jane@x.com')."""
    raw = decode_mime_header(raw).strip()
    m = re.match(r"^(.*?)<([^>]+)>$", raw)
    if m:
        return EmailAddress(name=m.group(1).strip().strip('"'), address=m.group(2).strip())
    return EmailAddress(name="", address=raw)


def _format_addresses(value: str | None) -> list[EmailAddress]:
    if not value:
        return []
    # Split on commas that are not inside angle brackets.
    parts, depth, buf = [], 0, ""
    for ch in value:
        if ch == "<":
            depth += 1
        elif ch == ">":
            depth = max(0, depth - 1)
        if ch == "," and depth == 0:
            parts.append(buf)
            buf = ""
        else:
            buf += ch
    parts.append(buf)
    return [_parse_address(p) for p in parts if p.strip()]


def _decode_body_data(data: str, encoding: str) -> str:
    enc = (encoding or "7bit").lower()
    if enc in {"base64", "urlsafe_base64"}:
        raw = _b64url_decode(re.sub(r"\s", "", data))
    elif enc == "quoted-printable":
        import quopri

        raw = quopri.decodestring(data.encode("utf-8", "replace"))
    else:
        return data
    for charset in ("utf-8", "latin-1"):
        try:
            return raw.decode(charset)
        except (UnicodeDecodeError, LookupError):
            continue
    return raw.decode("utf-8", "replace")


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------
class GmailService:
    """Calls the real Gmail API with a caller-supplied access token."""

    def __init__(self, client: httpx.AsyncClient | None = None):
        self._client = client

    async def _request(
        self, method: str, path: str, token: str, **kwargs
    ) -> dict:
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
        try:
            if self._client:
                resp = await self._client.request(
                    method, f"{GMAIL_BASE}{path}", headers=headers, **kwargs
                )
            else:
                async with httpx.AsyncClient(timeout=30) as client:
                    resp = await client.request(
                        method, f"{GMAIL_BASE}{path}", headers=headers, **kwargs
                    )
        except httpx.HTTPError as exc:
            logger.error("Gmail request failed (%s %s): network error", method, path)
            raise GmailError("Could not reach Gmail. Check your network.") from exc

        if resp.status_code == 401:
            raise GmailError(
                "Gmail authorization expired or was revoked. "
                "Reconnect your Google account."
            )
        if resp.status_code == 403:
            raise GmailError("Gmail denied access (quota or permission). Try again later.")
        if resp.status_code == 404:
            raise GmailError("Email not found in your mailbox.")
        if resp.status_code >= 400:
            logger.warning("Gmail API %s %s -> %s", method, path, resp.status_code)
            raise GmailError(f"Gmail API error (HTTP {resp.status_code}).")
        return resp.json()

    # --- list ---------------------------------------------------------------
    async def list_latest(
        self, token: str, *, max_results: int = 5, page_token: str | None = None,
        query: str | None = None,
    ) -> tuple[list[EmailSummary], str | None]:
        params: dict = {
            "maxResults": max(1, min(max_results, 50)),
            "fields": LIST_FIELDS,
        }
        if page_token:
            params["pageToken"] = page_token
        if query:
            params["q"] = query
        data = await self._request("GET", "/messages", token, params=params)

        summaries: list[EmailSummary] = []
        for item in data.get("messages", []):
            try:
                summaries.append(await self.get_summary(token, item["id"]))
            except GmailError:
                continue  # skip a single unreadable message, keep the rest
        return summaries, data.get("nextPageToken")

    async def get_summary(self, token: str, msg_id: str) -> EmailSummary:
        data = await self._request(
            "GET", f"/messages/{msg_id}", token,
            params={"format": "metadata", "metadataHeaders": "From,Subject,Date"},
        )
        return self._to_summary(data)

    def _to_summary(self, data: dict) -> EmailSummary:
        headers = {
            h.get("name", "").lower(): h.get("value", "")
            for h in data.get("payload", {}).get("headers", [])
        }
        sender = _parse_address(headers.get("from", ""))
        internal = data.get("internalDate")
        received = (
            datetime.fromtimestamp(int(internal) / 1000, tz=timezone.utc).replace(tzinfo=None)
            if internal
            else None
        )
        labels = data.get("labelIds", [])
        return EmailSummary(
            id=data.get("id", ""),
            thread_id=data.get("threadId", ""),
            sender_name=sender.name or sender.address,
            sender_email=sender.address,
            subject=decode_mime_header(headers.get("subject")) or "(no subject)",
            snippet=data.get("snippet", ""),
            received_at=received,
            is_unread="UNREAD" in labels,
        )

    # --- detail -------------------------------------------------------------
    async def get_detail(self, token: str, msg_id: str) -> EmailDetail:
        data = await self._request(
            "GET", f"/messages/{msg_id}", token, params={"format": "full"}
        )
        summary = self._to_summary(data)
        payload = data.get("payload", {})
        headers = {
            h.get("name", "").lower(): h.get("value", "")
            for h in payload.get("headers", [])
        }

        body_text, body_html = "", ""
        if payload.get("body", {}).get("data"):
            raw = _decode_body_data(payload["body"]["data"], payload["body"].get("encoding", "base64"))
            # Single-part message
            if headers.get("content-type", "").startswith("text/html"):
                body_html = raw
            else:
                body_text = raw
        else:
            # multipart: reconstruct from raw bytes for correct MIME handling
            body_text, body_html = await self._bodies_from_parts(token, data)

        sanitized = sanitize_html(body_html) if body_html else ""

        attachment_names = [
            p.get("filename")
            for p in payload.get("parts", [])
            if p.get("filename")
        ]

        return EmailDetail(
            **summary.model_dump(),
            to=_parse_address_list(headers.get("to", "")),
            body_text=body_text[:200_000],
            body_html_sanitized=sanitized[:400_000],
            label_ids=data.get("labelIds", []),
            attachments=[a for a in attachment_names if a][:20],
        )

    async def send(
        self, token: str, *, sender: str, recipient: str, subject: str, body: str
    ) -> dict[str, str]:
        """Send a plain-text message through the authenticated user's Gmail."""
        message = EmailMessage()
        if sender:
            message["From"] = sender
        message["To"] = recipient
        message["Subject"] = subject
        message.set_content(body)
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode("ascii").rstrip("=")
        return await self._request("POST", "/messages/send", token, json={"raw": raw})

    async def _bodies_from_parts(self, token: str, data: dict) -> tuple[str, str]:
        """Decode nested message parts using the Gmail payload tree."""
        payload = data.get("payload", {})
        parts = payload.get("parts", [])
        if not parts:
            body = payload.get("body", {})
            if body.get("data"):
                raw = _decode_body_data(body["data"], body.get("encoding", "base64"))
                return raw, ""
            return "", ""

        text_out: list[str] = []
        html_out: list[str] = []

        def visit(part: dict) -> None:
            mime = (part.get("mimeType") or "").lower()
            filename = part.get("filename", "")
            if part.get("parts"):
                for child in part["parts"]:
                    visit(child)
                return
            body = part.get("body", {})
            data_b64 = body.get("data")
            if not data_b64:
                return
            if filename and not mime.startswith("text/"):
                return  # attachment, not body
            content = _decode_body_data(data_b64, body.get("encoding", "base64"))
            if mime == "text/plain":
                text_out.append(content)
            elif mime == "text/html":
                html_out.append(content)

        for p in parts:
            visit(p)

        return "\n".join(text_out).strip(), "\n".join(html_out).strip()

    # --- search (used by the agent's search_emails tool) --------------------
    async def search(
        self, token: str, query: str, *, max_results: int = 10
    ) -> tuple[list[EmailSummary], str | None]:
        return await self.list_latest(
            token, max_results=max_results, query=query
        )


def _parse_address_list(raw: str) -> list[EmailAddress]:
    return _format_addresses(raw)
