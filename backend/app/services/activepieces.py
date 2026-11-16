import httpx
from typing import List, Dict, Optional
from dataclasses import dataclass

from app.config import settings


@dataclass
class EmailSummary:
    id: str
    subject: str
    from_: str
    date: str
    snippet: str


@dataclass
class EmailDetail:
    id: str
    subject: str
    from_: str
    date: str
    body: str
    snippet: str


class ActivepiecesService:
    def __init__(self):
        self.api_key = settings.ACTIVEPIECES_API_KEY
        self.base_url = settings.ACTIVEPIECES_BASE_URL.rstrip("/")
        self.search_flow_id = settings.ACTIVEPIECES_SEARCH_FLOW_ID
        self.get_flow_id = settings.ACTIVEPIECES_GET_FLOW_ID
        self.client = httpx.AsyncClient(timeout=30.0)

    def is_configured(self) -> bool:
        return bool(self.api_key and self.search_flow_id and self.get_flow_id)

    async def search_emails(
        self,
        query: str = "",
        max_results: int = 50,
        page_token: Optional[str] = None,
    ) -> Dict:
        """Search emails via Activepieces sync webhook."""
        if not self.is_configured():
            raise ValueError("Activepieces not configured")

        payload = {
            "query": query,
            "maxResults": max_results,
        }
        if page_token:
            payload["pageToken"] = page_token

        response = await self.client.post(
            f"{self.base_url}/webhooks/{self.search_flow_id}/sync",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )

        if response.status_code != 200:
            raise Exception(f"Activepieces search failed: {response.status_code} - {response.text}")

        return response.json()

    async def get_email(self, email_id: str) -> Optional[EmailDetail]:
        """Get full email detail via Activepieces sync webhook."""
        if not self.is_configured():
            raise ValueError("Activepieces not configured")

        response = await self.client.post(
            f"{self.base_url}/webhooks/{self.get_flow_id}/sync",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={"emailId": email_id},
        )

        if response.status_code != 200:
            raise Exception(f"Activepieces get failed: {response.status_code} - {response.text}")

        data = response.json()
        if not data:
            return None

        return EmailDetail(
            id=data.get("id", email_id),
            subject=data.get("subject", ""),
            from_=data.get("from", ""),
            date=data.get("date", ""),
            body=data.get("body", ""),
            snippet=data.get("snippet", data.get("body", "")[:200]),
        )

    def parse_search_response(self, response: Dict) -> tuple[List[EmailSummary], Optional[str]]:
        """Parse Activepieces search response into EmailSummary list."""
        emails = response.get("emails", [])
        next_page_token = response.get("nextPageToken")

        summaries = [
            EmailSummary(
                id=e.get("id", ""),
                subject=e.get("subject", ""),
                from_=e.get("from", ""),
                date=e.get("date", ""),
                snippet=e.get("snippet", e.get("body", "")[:200]),
            )
            for e in emails
        ]

        return summaries, next_page_token

    async def close(self):
        await self.client.aclose()


_activepieces_service: Optional[ActivepiecesService] = None


def get_activepieces_service() -> ActivepiecesService:
    global _activepieces_service
    if _activepieces_service is None:
        _activepieces_service = ActivepiecesService()
    return _activepieces_service