"""Email API: proxies real Gmail data to the frontend (sanitized)."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..config import get_settings
from ..database import get_db
from ..models import User
from ..schemas import EmailDetail, EmailListResponse
from ..services.activepieces_service import ActivepiecesError, get_activepieces_service
from ..services.gmail_service import GmailError, GmailService
from ..services.google_oauth import OAuthError
from ..services.token_service import TokenService
from .deps import get_session_user

router = APIRouter(prefix="/api/emails", tags=["emails"])
logger = logging.getLogger(__name__)

settings = get_settings()


async def _gmail_token(user: User, db: Session) -> str:
    """Resolve a currently-valid access token or raise a friendly error."""
    try:
        return await TokenService().get_valid_access_token(db, user.id)
    except OAuthError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


def _provider_for(user: User, db: Session) -> str:
    """Determine mail provider: activepieces > google > none."""
    # Activepieces configured globally?
    if settings.activepieces_api_key and settings.activepieces_search_flow_id:
        return "activepieces"
    # Google OAuth connected for this user?
    from ..services.token_service import TokenService
    tok = TokenService().get_integration(db, user.id)
    if tok and tok.provider == "google" and tok.encrypted_access_token:
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
    """Latest emails from the connected mail provider (actual API, never mock)."""
    provider = _provider_for(user, db)
    
    if provider == "activepieces":
        svc = get_activepieces_service()
        try:
            emails = svc.list_latest(user.id, max_results=limit)
        except ActivepiecesError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.message)
        return EmailListResponse(emails=emails, next_page_token=None)
    
    if provider == "google":
        token = await _gmail_token(user, db)
        gmail = GmailService()
        try:
            emails, next_token = await gmail.list_latest(
                token, max_results=limit, page_token=page_token, query=q
            )
        except GmailError as exc:
            raise HTTPException(status_code=502, detail=str(exc))
        return EmailListResponse(emails=emails, next_page_token=next_token)
    
    raise HTTPException(
        status_code=409,
        detail="No mail provider configured. Connect Google or enable Activepieces."
    )


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
        svc = get_activepieces_service()
        try:
            return svc.get_detail(user.id, email_id)
        except ActivepiecesError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.message)
    
    if provider == "google":
        token = await _gmail_token(user, db)
        gmail = GmailService()
        try:
            return await gmail.get_detail(token, email_id)
        except GmailError as exc:
            raise HTTPException(status_code=502, detail=str(exc))
    
    raise HTTPException(
        status_code=409,
        detail="No mail provider configured. Connect Google or enable Activepieces."
    )
