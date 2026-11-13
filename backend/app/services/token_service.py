"""Token storage & lifecycle: encryption at rest, automatic refresh.

Tokens are Fernet-encrypted before hitting the database and decrypted only
in memory at the moment a Gmail call needs them. Refresh tokens are never
returned by any API response.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Integration
from ..security.encryption import decrypt, encrypt
from .google_oauth import OAuthError, TokenBundle, GoogleOAuthService

logger = logging.getLogger(__name__)

PROVIDER = "google"
REFRESH_SKEW = timedelta(minutes=5)


class TokenService:
    def __init__(self, oauth: GoogleOAuthService | None = None):
        self.oauth = oauth or GoogleOAuthService()

    def upsert_integration(
        self,
        db: Session,
        *,
        user_id: str,
        bundle: TokenBundle,
        provider_email: str = "",
    ) -> Integration:
        """Store (or replace) the encrypted credential row for a user."""
        row = db.scalar(
            select(Integration).where(
                Integration.user_id == user_id,
                Integration.provider == PROVIDER,
            )
        )
        if row is None:
            row = Integration(user_id=user_id, provider=PROVIDER)
            db.add(row)

        row.provider_email = provider_email
        row.encrypted_access_token = encrypt(bundle.access_token)
        if bundle.refresh_token:
            row.encrypted_refresh_token = encrypt(bundle.refresh_token)
        row.token_expiry = bundle.expiry_datetime
        row.scopes = bundle.scope
        row.connected_at = datetime.utcnow()
        db.commit()
        db.refresh(row)
        return row

    def get_integration(self, db: Session, user_id: str) -> Integration | None:
        return db.scalar(
            select(Integration).where(
                Integration.user_id == user_id,
                Integration.provider == PROVIDER,
            )
        )

    def disconnect(self, db: Session, user_id: str) -> bool:
        """Securely remove stored credentials (revokes nothing at Google —
        users can revoke access at myaccount.google.com/permissions)."""
        row = self.get_integration(db, user_id)
        if row is None:
            return False
        db.delete(row)
        db.commit()
        return True

    async def get_valid_access_token(
        self, db: Session, user_id: str
    ) -> str:
        """Return a valid access token, transparently refreshing if expired.

        Raises OAuthError when the integration is missing/disconnected or
        cannot be refreshed (user must reconnect).
        """
        row = self.get_integration(db, user_id)
        if row is None:
            raise OAuthError(
                "Gmail is not connected. Connect your Google account first."
            )

        needs_refresh = (
            row.token_expiry is None
            or datetime.utcnow() >= row.token_expiry - REFRESH_SKEW
        )
        if not needs_refresh:
            return decrypt(row.encrypted_access_token)

        refresh_token = decrypt(row.encrypted_refresh_token)
        if not refresh_token:
            raise OAuthError(
                "Stored Gmail credentials have no refresh token. "
                "Please reconnect Gmail."
            )
        try:
            bundle = await self.oauth.refresh_access_token(refresh_token)
        except OAuthError:
            logger.warning("Token refresh failed for user; reconnect required")
            raise

        row.encrypted_access_token = encrypt(bundle.access_token)
        row.token_expiry = bundle.expiry_datetime
        db.commit()
        return bundle.access_token
