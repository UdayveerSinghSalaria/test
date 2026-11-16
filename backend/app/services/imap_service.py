import imaplib
import email
from email.header import decode_header
from typing import List, Dict, Optional
from dataclasses import dataclass
import re
from datetime import datetime, timedelta

from app.services.encryption import decrypt
from app.models.email_account import EmailAccount


@dataclass
class EmailMessage:
    id: str
    subject: str
    from_: str
    date: str
    body: str
    snippet: str


class IMAPService:
    PROVIDER_CONFIG = {
        "gmail": {"imap_host": "imap.gmail.com", "imap_port": 993, "smtp_host": "smtp.gmail.com", "smtp_port": 587},
        "yahoo": {"imap_host": "imap.mail.yahoo.com", "imap_port": 993, "smtp_host": "smtp.mail.yahoo.com", "smtp_port": 587},
        "outlook": {"imap_host": "outlook.office365.com", "imap_port": 993, "smtp_host": "smtp.office365.com", "smtp_port": 587},
    }

    def __init__(self, email_account: EmailAccount):
        self.account = email_account
        self.app_password = decrypt(email_account.app_password_encrypted)

    def _connect(self) -> imaplib.IMAP4_SSL:
        """Create IMAP connection."""
        conn = imaplib.IMAP4_SSL(self.account.imap_host, self.account.imap_port)
        conn.login(self.account.email_address, self.app_password)
        return conn

    def fetch_recent(
        self,
        limit: int = 50,
        since_days: int = 7,
        folder: str = "INBOX",
    ) -> List[EmailMessage]:
        """Fetch recent emails from the inbox."""
        conn = self._connect()
        try:
            conn.select(folder)

            # Search for recent emails
            date_str = (datetime.now() - timedelta(days=since_days)).strftime("%d-%b-%Y")
            status, messages = conn.search(None, f'(SINCE "{date_str}")')

            if status != "OK":
                return []

            email_ids = messages[0].split()[-limit:]
            emails = []

            for eid in reversed(email_ids):
                try:
                    status, msg_data = conn.fetch(eid, "(RFC822)")
                    if status != "OK":
                        continue

                    raw = msg_data[0][1]
                    msg = email.message_from_bytes(raw)

                    emails.append(EmailMessage(
                        id=eid.decode(),
                        subject=self._decode_header(msg["Subject"]),
                        from_=msg["From"] or "",
                        date=msg["Date"] or "",
                        body=self._get_body(msg),
                        snippet=self._get_body(msg)[:200],
                    ))
                except Exception as e:
                    print(f"[IMAP] Error fetching email {eid}: {e}")
                    continue

            return emails
        finally:
            try:
                conn.close()
                conn.logout()
            except Exception:
                pass

    def fetch_one(self, email_id: str, folder: str = "INBOX") -> Optional[EmailMessage]:
        """Fetch a single email by ID."""
        conn = self._connect()
        try:
            conn.select(folder)
            status, msg_data = conn.fetch(email_id.encode(), "(RFC822)")

            if status != "OK":
                return None

            raw = msg_data[0][1]
            msg = email.message_from_bytes(raw)

            return EmailMessage(
                id=email_id,
                subject=self._decode_header(msg["Subject"]),
                from_=msg["From"] or "",
                date=msg["Date"] or "",
                body=self._get_body(msg),
                snippet=self._get_body(msg)[:200],
            )
        finally:
            try:
                conn.close()
                conn.logout()
            except Exception:
                pass

    def _decode_header(self, header: str) -> str:
        """Decode email header."""
        if not header:
            return ""
        try:
            parts = decode_header(header)
            return "".join(
                part.decode(enc or "utf-8") if isinstance(part, bytes) else part
                for part, enc in parts
            )
        except Exception:
            return header

    def _get_body(self, msg) -> str:
        """Extract text body from email."""
        try:
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    if content_type == "text/plain":
                        payload = part.get_payload(decode=True)
                        if payload:
                            return payload.decode(errors="ignore")
                    elif content_type == "text/html" and not hasattr(self, "_html_body"):
                        # Fallback to HTML if no plain text
                        payload = part.get_payload(decode=True)
                        if payload:
                            self._html_body = payload.decode(errors="ignore")
                # Return HTML if no plain text found
                if hasattr(self, "_html_body"):
                    html = self._html_body
                    delattr(self, "_html_body")
                    return self._html_to_text(html)
                return ""
            else:
                payload = msg.get_payload(decode=True)
                if payload:
                    return payload.decode(errors="ignore")
                return ""
        except Exception:
            return ""

    def _html_to_text(self, html: str) -> str:
        """Basic HTML to text conversion."""
        # Remove scripts and styles
        html = re.sub(r"<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>", " ", html, flags=re.IGNORECASE)
        html = re.sub(r"<style\b[^<]*(?:(?!<\/style>)<[^<]*)*<\/style>", " ", html, flags=re.IGNORECASE)
        # Replace tags with spaces
        html = re.sub(r"<[^>]+>", " ", html)
        # Clean whitespace
        html = re.sub(r"\s+", " ", html)
        return html.strip()

    @classmethod
    def get_provider_config(cls, provider: str) -> Dict[str, any]:
        """Get IMAP/SMTP config for a provider."""
        return cls.PROVIDER_CONFIG.get(provider, cls.PROVIDER_CONFIG["gmail"])