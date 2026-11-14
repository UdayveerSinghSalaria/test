"""Activepieces mail service — thin wrapper around sync webhook calls.

Uses pre-configured flows (IDs from .env). No provisioning logic at runtime.
"""
from __future__ import annotations

import json
import re
import httpx
from typing import Optional
from datetime import datetime
from email.utils import getaddresses, parseaddr
from html import unescape

from app.config import get_settings
from app.schemas import EmailAddress, EmailDetail, EmailSummary
from app.services.gmail_service import sanitize_html

settings = get_settings()


class ActivepiecesError(Exception):
    """Raised when Activepieces webhook call fails."""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class ActivepiecesService:
    """Client for calling Activepieces sync webhooks."""

    def __init__(self) -> None:
        self.base_url = settings.activepieces_base_url.rstrip("/")
        self.api_key = settings.activepieces_api_key
        self.search_flow_id = settings.activepieces_search_flow_id
        self.get_flow_id = settings.activepieces_get_flow_id

    @property
    def is_configured(self) -> bool:
        return all([
            self.api_key,
            self.search_flow_id,
            self.get_flow_id,
        ])

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _call_sync(self, flow_id: str, body: dict) -> dict:
        """Call sync webhook, return parsed JSON body."""
        url = f"{self.base_url}/webhooks/{flow_id}/sync"
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(url, headers=self._headers(), json=body)
        
        if resp.status_code == 404:
            raise ActivepiecesError("Flow not found or disabled", 404)
        if resp.status_code == 402:
            raise ActivepiecesError("Activepieces credits exhausted (402)", 402)
        if resp.status_code == 408:
            raise ActivepiecesError("Webhook timeout (408)", 408)
        if resp.status_code >= 500:
            raise ActivepiecesError(f"Activepieces server error: {resp.status_code}", resp.status_code)
        if resp.status_code != 200:
            raise ActivepiecesError(f"Webhook failed: {resp.status_code} {resp.text}", resp.status_code)
        
        try:
            return resp.json()
        except json.JSONDecodeError:
            raise ActivepiecesError("Invalid JSON response from webhook", 500)

    # ---- Public API matching gmail_service surface --------------------------

    def list_latest(self, user_id: int, max_results: int = 20) -> list[EmailSummary]:
        """Fetch latest emails (maps to search with no filters)."""
        if not self.is_configured:
            raise ActivepiecesError("Activepieces not configured", 409)
        
        body = {"max_results": max_results}
        data = self._call_sync(self.search_flow_id, body)
        
        # Expected shape: {"found": bool, "results": {"messages": [...], "count": int}}
        # Each message has: id, subject, from, to, date, text, html, attachments
        messages = self._extract_messages(data)
        return [self._to_summary(m) for m in messages]

    def search(
        self,
        user_id: int,
        q: str = "",
        max_results: int = 20,
        label: Optional[str] = None,
    ) -> list[EmailSummary]:
        """Search emails - translates Gmail-like query to structured filters."""
        if not self.is_configured:
            raise ActivepiecesError("Activepieces not configured", 409)
        
        # Parse simple query string into structured filters
        # q format examples: "from:alice subject:invoice after:2024-01-01"
        filters = self._parse_query(q)
        filters["max_results"] = max_results
        if label:
            filters["label"] = label
        
        data = self._call_sync(self.search_flow_id, filters)
        messages = self._extract_messages(data)
        return [self._to_summary(m) for m in messages]

    def get_detail(self, user_id: int, message_id: str) -> EmailDetail:
        """Fetch full email detail by message ID."""
        if not self.is_configured:
            raise ActivepiecesError("Activepieces not configured", 409)
        
        body = {"message_id": message_id}
        data = self._call_sync(self.get_flow_id, body)
        
        # Expected shape: {id, subject, from, to, cc, date, text, html, attachments, messageId, ...}
        return self._to_detail(data)

    # ---- Internal helpers ----------------------------------------------------

    def _parse_query(self, q: str) -> dict:
        """Parse Gmail-style query string into structured filters."""
        filters = {}
        if not q:
            return filters
        
        parts = q.split()
        for part in parts:
            if part.startswith("from:"):
                filters["from"] = part[5:].strip('"')
            elif part.startswith("to:"):
                filters["to"] = part[3:].strip('"')
            elif part.startswith("subject:"):
                filters["subject"] = part[8:].strip('"')
            elif part.startswith("after:"):
                filters["after_date"] = part[6:]
            elif part.startswith("before:"):
                filters["before_date"] = part[7:]
            elif part == "has:attachment":
                filters["has_attachment"] = True
            elif part.startswith("label:"):
                filters["label"] = part[6:]
            elif part.startswith("category:"):
                filters["category"] = part[9:]
            elif part.startswith("in:") and part[3:].lower() == "inbox":
                filters["label"] = "INBOX"
            elif part.startswith("content:"):
                filters["content"] = part[8:].strip('"')
            elif " " not in part and "@" in part:
                # bare email -> treat as from
                filters["from"] = part
            elif not part.startswith(("is:", "in:")):
                filters.setdefault("content", "")
                filters["content"] = f"{filters['content']} {part.strip(chr(34))}".strip()
        
        return filters

    def _to_summary(self, m: dict) -> EmailSummary:
        """Map Activepieces message to EmailSummary."""
        # m shape: {id, subject, from: {text, value}, to: {text, value}, date, text, html, attachments, messageId}
        sender_name, sender_email = self._sender(m.get("from"))
        received_at = self._date(m.get("date"))
        snippet = self._snippet(m.get("text") or m.get("html") or "")
        
        return EmailSummary(
            id=m.get("id", ""),
            thread_id=m.get("threadId", m.get("id", "")),
            sender_name=sender_name,
            sender_email=sender_email,
            subject=m.get("subject", "(no subject)"),
            snippet=snippet,
            received_at=received_at,
            is_unread=False,
        )

    def _to_detail(self, m: dict) -> EmailDetail:
        """Map Activepieces message to EmailDetail."""
        summary = self._to_summary(m)
        attachments = [
            item.get("fileName", "attachment") if isinstance(item, dict) else str(item)
            for item in m.get("attachments", [])
        ]
        return EmailDetail(
            **summary.model_dump(),
            to=self._addresses(m.get("to")),
            body_text=str(m.get("text") or ""),
            body_html_sanitized=sanitize_html(str(m.get("html") or "")),
            attachments=attachments,
        )

    @staticmethod
    def _sender(value) -> tuple[str, str]:
        if isinstance(value, dict):
            text = value.get("text", "")
            if text:
                value = text
            else:
                addresses = ActivepiecesService._addresses(value)
                if addresses:
                    return addresses[0].name or addresses[0].address, addresses[0].address
                value = ""
        name, address = parseaddr(str(value or ""))
        return name or address, address

    @staticmethod
    def _addresses(value) -> list[EmailAddress]:
        if isinstance(value, dict):
            value = value.get("value") or value.get("text", "")
        if isinstance(value, list):
            pairs = [
                (
                    str(item.get("name", "")),
                    str(item.get("address") or item.get("email") or ""),
                )
                for item in value
                if isinstance(item, dict)
            ]
        else:
            pairs = getaddresses([str(value or "")])
        return [EmailAddress(name=name, address=address) for name, address in pairs if address]

    @staticmethod
    def _date(value) -> datetime | None:
        if not isinstance(value, str) or not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None

    @staticmethod
    def _snippet(value: str) -> str:
        safe_html = sanitize_html(str(value))
        return unescape(re.sub(r"<[^>]+>", " ", safe_html))[:200].strip()

    @staticmethod
    def _extract_messages(data: dict) -> list[dict]:
        if data.get("found") is False:
            return []
        results = data.get("results", data)
        if isinstance(results, list):
            return [item for item in results if isinstance(item, dict)]
        if isinstance(results, dict):
            messages = results.get("messages", [])
            if isinstance(messages, list):
                return [item for item in messages if isinstance(item, dict)]
        return []


# Singleton
_activepieces_service: Optional[ActivepiecesService] = None


def get_activepieces_service() -> ActivepiecesService:
    global _activepieces_service
    if _activepieces_service is None:
        _activepieces_service = ActivepiecesService()
    return _activepieces_service