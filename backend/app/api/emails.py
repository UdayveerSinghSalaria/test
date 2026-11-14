"""Email API: proxies the configured mail provider to the frontend (sanitized)."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..schemas import (
    EmailDetail,
    EmailListResponse,
    EmailSendRequest,
    EmailSentResponse,
)
from ..services.gmail_service import GmailError, GmailService
from ..services.activepieces_service import ActivepiecesError, get_activepieces_service
from ..services.google_oauth import OAuthError
from ..services.token_service import TokenService
from .deps import get_session_user

router = APIRouter(prefix="/api/emails", tags=["emails"])
logger = logging.getLogger(__name__)


async def _gmail_token(user: User, db: Session) -> str:
    """Resolve a currently-valid access token or raise a friendly error."""
    try:
        return await TokenService().get_valid_access_token(db, user.id)
    except OAuthError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


def _provider_for(user: User, db: Session) -> str:
    """Prefer the allowlisted Activepieces mailbox; otherwise use user Gmail."""
    activepieces = get_activepieces_service()
    if activepieces.is_configured:
        if not activepieces.is_allowed_user(user.email):
            raise HTTPException(
                status_code=403,
                detail="The Activepieces mailbox is restricted to its configured SaarthiFlow account.",
            )
        return "activepieces"
    integration = TokenService().get_integration(db, user.id)
    if integration and integration.encrypted_access_token:
        return "google"
    return "none"


@router.get("", response_model=EmailListResponse)
async def list_emails(
    limit: int = Query(default=5, ge=1, le=50),
    page_token: str | None = Query(default=None),
    q: str | None = Query(default=None, max_length=500),
    user: User = Depends(get_session_user),
    db: Session = Depends(get_db),
) -> EmailListResponse:
    """Latest messages from the configured mailbox."""
    provider = _provider_for(user, db)
    if provider == "activepieces":
        service = get_activepieces_service()
        try:
            emails = (
                service.search(user.id, q=q, max_results=limit)
                if q
                else service.list_latest(user.id, max_results=limit)
            )
        except ActivepiecesError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.message)
        return EmailListResponse(emails=emails, next_page_token=None)
    if provider != "google":
        raise HTTPException(
            status_code=409,
            detail="No mail provider is configured. Connect Google or configure your Activepieces mailbox.",
        )

    token = await _gmail_token(user, db)
    try:
        emails, next_token = await GmailService().list_latest(
            token, max_results=limit, page_token=page_token, query=q
        )
    except GmailError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    return EmailListResponse(emails=emails, next_page_token=next_token)


@router.get("/{email_id}", response_model=EmailDetail)
async def get_email(
    email_id: str,
    user: User = Depends(get_session_user),
    db: Session = Depends(get_db),
) -> EmailDetail:
    """Full message: multipart-decoded text + sanitized HTML."""
    # Basic id sanity check — Gmail ids are alphanumeric with - and _
    if not email_id or len(email_id) > 128 or not all(
        c.isalnum() or c in "-_" for c in email_id
    ):
        raise HTTPException(status_code=400, detail="Invalid email id.")

    provider = _provider_for(user, db)
    if provider == "activepieces":
        try:
            return get_activepieces_service().get_detail(user.id, email_id)
        except ActivepiecesError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.message)
    if provider != "google":
        raise HTTPException(
            status_code=409,
            detail="No mail provider is configured. Connect Google or configure your Activepieces mailbox.",
        )

    token = await _gmail_token(user, db)
    try:
        return await GmailService().get_detail(token, email_id)
    except GmailError as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.post("/send", response_model=EmailSentResponse)
async def send_email(
    payload: EmailSendRequest,
    user: User = Depends(get_session_user),
    db: Session = Depends(get_db),
) -> EmailSentResponse:
    """Send a plain-text email through a user's Google account."""
    if _provider_for(user, db) == "activepieces":
        raise HTTPException(
            status_code=409,
            detail="Send from Agent Studio so the message can be approved first.",
        )
    integration = TokenService().get_integration(db, user.id)
    send_scope = "https://www.googleapis.com/auth/gmail.send"
    if integration is None:
        raise HTTPException(
            status_code=409, detail="Connect your Google account before sending mail."
        )
    if send_scope not in integration.scopes.split():
        raise HTTPException(
            status_code=409,
            detail="Gmail send permission is missing. Reconnect Google and approve the send permission.",
        )

    token = await _gmail_token(user, db)
    try:
        result = await GmailService().send(
            token,
            sender=integration.provider_email,
            recipient=str(payload.to),
            subject=payload.subject,
            body=payload.body,
        )
    except GmailError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    message_id = result.get("id")
    if not message_id:
        raise HTTPException(status_code=502, detail="Gmail did not confirm the sent message.")
    return EmailSentResponse(id=message_id, thread_id=result.get("threadId", ""))
