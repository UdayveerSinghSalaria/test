from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import uuid

from app.database import get_db
from app.config import settings
from app.services.imap_service import IMAPService
from app.services.smtp_service import SMTPService
from app.services.activepieces import ActivepiecesService, get_activepieces_service
from app.services.encryption import encrypt
from app.models.email_account import EmailAccount, EmailProvider
from app.schemas.email import (
    EmailAccountCreate, EmailAccountResponse,
    EmailFetchRequest, EmailFetchResponse, EmailItem,
    EmailSendRequest, EmailSendResponse,
)
from app.dependencies import get_current_user, get_db_session
from app.models.user import User

router = APIRouter(prefix="/emails", tags=["Emails"])


@router.post("/accounts", response_model=EmailAccountResponse, status_code=201)
async def add_email_account(
    account_data: EmailAccountCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Add an email account with IMAP/SMTP credentials."""
    # Check if already exists for this user
    existing = await db.execute(
        select(EmailAccount).where(EmailAccount.user_id == current_user.id, EmailAccount.email_address == account_data.email_address)
    )
    if existing.scalars().first():
        raise HTTPException(status_code=400, detail="Email account already exists")

    # Get provider config
    provider_config = IMAPService.get_provider_config(account_data.provider)

    account = EmailAccount(
        id=f"ea-{uuid.uuid4().hex[:12]}",
        user_id=current_user.id,
        provider=EmailProvider(account_data.provider),
        email_address=account_data.email_address,
        app_password_encrypted=encrypt(account_data.app_password),
        imap_host=provider_config["imap_host"],
        imap_port=str(provider_config["imap_port"]),
        smtp_host=provider_config["smtp_host"],
        smtp_port=str(provider_config["smtp_port"]),
        is_active="true",
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return EmailAccountResponse(**account.to_dict())


@router.get("/accounts", response_model=List[EmailAccountResponse])
async def get_email_accounts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Get all configured email accounts."""
    result = await db.execute(select(EmailAccount).where(EmailAccount.user_id == current_user.id))
    accounts = result.scalars().all()
    return [EmailAccountResponse(**a.to_dict()) for a in accounts]


@router.delete("/accounts/{account_id}")
async def delete_email_account(
    account_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Delete an email account."""
    result = await db.execute(select(EmailAccount).where(EmailAccount.id == account_id, EmailAccount.user_id == current_user.id))
    account = result.scalars().first()
    if not account:
        raise HTTPException(status_code=404, detail="Email account not found")

    await db.delete(account)
    await db.commit()
    return {"message": "Email account deleted"}


@router.post("/fetch", response_model=EmailFetchResponse)
async def fetch_emails(
    request: EmailFetchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Fetch emails from the user's inbox (uses IMAP or Activepieces fallback)."""
    # Try to get user's email account
    result = await db.execute(
        select(EmailAccount).where(EmailAccount.user_id == current_user.id, EmailAccount.is_active == "true")
    )
    account = result.scalars().first()

    if account:
        # Use IMAP
        try:
            imap_service = IMAPService(account)
            emails = imap_service.fetch_recent(
                limit=request.limit,
                since_days=request.since_days,
                folder=request.folder,
            )
            return EmailFetchResponse(
                emails=[
                    EmailItem(
                        id=e.id,
                        subject=e.subject,
                        from_=e.from_,
                        date=e.date,
                        body=e.body,
                        snippet=e.snippet,
                    )
                    for e in emails
                ],
                count=len(emails),
            )
        except Exception as e:
            print(f"[IMAP] Fetch failed, trying Activepieces fallback: {e}")

    # Fallback to Activepieces
    activepieces = get_activepieces_service()
    if activepieces.is_configured():
        try:
            response = await activepieces.search_emails(
                query="",
                max_results=request.limit,
            )
            summaries, _ = activepieces.parse_search_response(response)
            return EmailFetchResponse(
                emails=[
                    EmailItem(
                        id=e.id,
                        subject=e.subject,
                        from_=e.from_,
                        date=e.date,
                        body=e.snippet,  # Only snippet available from search
                        snippet=e.snippet,
                    )
                    for e in summaries
                ],
                count=len(summaries),
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Email fetch failed: {str(e)}")

    raise HTTPException(
        status_code=409,
        detail="No email account configured and Activepieces not available. Add an email account in Settings."
    )


@router.post("/send", response_model=EmailSendResponse)
async def send_email(
    request: EmailSendRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Send an email via SMTP."""
    result = await db.execute(
        select(EmailAccount).where(EmailAccount.user_id == current_user.id, EmailAccount.is_active == "true")
    )
    account = result.scalars().first()

    if not account:
        raise HTTPException(status_code=409, detail="No email account configured. Add one in Settings.")

    smtp_service = SMTPService(account)
    success = await smtp_service.send_email(
        to=request.to,
        subject=request.subject,
        body=request.body,
        html_body=request.html_body,
    )

    if not success:
        raise HTTPException(status_code=500, detail="Failed to send email")

    return EmailSendResponse(success=True, message="Email sent successfully")