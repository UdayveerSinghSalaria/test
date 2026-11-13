"""Activepieces mail service — thin wrapper around sync webhook calls.

Uses pre-configured flows (IDs from .env). No provisioning logic at runtime.
"""
from __future__ import annotations

import json
import httpx
from typing import Any, Optional
from datetime import datetime

from app.config import get_settings
from app.services.gmail_service import sanitize_html, EmailSummary, EmailDetail

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
        found = data.get("found", False)
        messages = data.get("results", {}).get("messages", []) if found else []
        
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
        found = data.get("found", False)
        messages = data.get("results", {}).get("messages", []) if found else []
        
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
            elif " " not in part and "@" in part:
                # bare email -> treat as from
                filters["from"] = part
        
        return filters

    def _to_summary(self, m: dict) -> EmailSummary:
        """Map Activepieces message to EmailSummary."""
        # m shape: {id, subject, from: {text, value}, to: {text, value}, date, text, html, attachments, messageId}
        from_text = ""
        if isinstance(m.get("from"), dict):
            from_text = m["from"].get("text", "")
        elif isinstance(m.get("from"), str):
            from_text = m["from"]
        
        to_text = ""
        if isinstance(m.get("to"), dict):
            to_text = m["to"].get("text", "")
        elif isinstance(m.get("to"), str):
            to_text = m["to"]
        
        date_str = m.get("date", "")
        try:
            # Activepieces returns ISO string
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            date_iso = dt.isoformat()
        except Exception:
            date_iso = datetime.utcnow().isoformat()
        
        snippet = m.get("text", "") or m.get("html", "") or ""
        snippet = sanitize_html(snippet)[:200]
        
        return EmailSummary(
            id=m.get("id", ""),
            thread_id=m.get("threadId", m.get("id", "")),
            subject=m.get("subject", "(no subject)"),
            from_email=from_text,
            to_email=to_text,
            date=date_iso,
            snippet=snippet,
            is_unread=True,  # Activepieces search doesn't return label info
            labels=[],
        )

    def _to_detail(self, m: dict) -> EmailDetail:
        """Map Activepieces message to EmailDetail."""
        from_text = ""
        from_value = []
        if isinstance(m.get("from"), dict):
            from_text = m["from"].get("text", "")
            val = m["from"].get("value", [])
            if isinstance(val, list):
                from_value = val
        elif isinstance(m.get("from"), str):
            from_text = m["from"]
        
        to_text = ""
        to_value = []
        if isinstance(m.get("to"), dict):
            to_text = m["to"].get("text", "")
            val = m["to"].get("value", [])
            if isinstance(val, list):
                to_value = val
        elif isinstance(m.get("to"), str):
            to_text = m["to"]
        
        date_str = m.get("date", "")
        try:
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            date_iso = dt.isoformat()
        except Exception:
            date_iso = datetime.utcnow().isoformat()
        
        attachments = []
        for att in m.get("attachments", []):
            if isinstance(att, dict):
                attachments.append({
                    "id": att.get("fileName", ""),
                    "filename": att.get("fileName", "attachment"),
                    "mime_type": att.get("mimeType", "application/octet-stream"),
                    "size": att.get("size", 0),
                })
        
        return EmailDetail(
            id=m.get("id", ""),
            thread_id=m.get("threadId", m.get("id", "")),
            subject=m.get("subject", "(no subject)"),
            from_email=from_text,
            to_email=to_text,
            date=date_iso,
            body_text=m.get("text", ""),
            body_html=sanitize_html(m.get("html", "")),
            attachments=attachments,
            message_id=m.get("messageId", m.get("id", "")),
            labels=[],
        )


# Singleton
_activepieces_service: Optional[ActivepiecesService] = None


def get_activepieces_service() -> ActivepiecesService:
    global _activepieces_service
    if _activepieces_service is None:
        _activepieces_service = ActivepiecesService()
    return _activepieces_service