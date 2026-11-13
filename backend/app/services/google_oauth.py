"""Google OAuth 2.0 Authorization Code Flow (backend only).

Flow:
  GET /api/integrations/google/connect
      -> random state (CSRF) stored in a short-lived signed cookie
      -> 302 to Google's official consent screen
  GET /api/integrations/google/callback?state=...&code=...
      -> state validated, code exchanged server-side for tokens
      -> tokens encrypted and stored, user redirected to the Integrations page

Security invariants enforced here:
  * The client secret never leaves the backend.
  * The OAuth `state` is generated with secrets.token_urlsafe and verified
    on return (CSRF protection).
  * Redirect URI is exactly the configured value; no wildcards.
  * Scope is fixed to readonly Gmail + openid/email/profile.
"""

from __future__ import annotations

import logging
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta
from urllib.parse import urlencode

import httpx

from ..config import Settings, get_settings

logger = logging.getLogger(__name__)

STATE_COOKIE = "awa_oauth_state"
STATE_MAX_AGE = 600  # 10 minutes

# Never requested in this milestone: any write/send scope.
READONLY_GMAIL_SCOPES = [
    "openid",
    "email",
    "profile",
    "https://www.googleapis.com/auth/gmail.readonly",
]


class OAuthError(Exception):
    """User-facing OAuth failure (bad state, denied consent, exchange error)."""


@dataclass
class TokenBundle:
    access_token: str
    refresh_token: str | None
    expires_in: int | None
    scope: str
    token_type: str = "Bearer"

    @property
    def expiry_datetime(self) -> datetime | None:
        if self.expires_in is None:
            return None
        return datetime.utcnow() + timedelta(seconds=self.expires_in - 60)


class GoogleOAuthService:
    def __init__(self, settings: Settings | None = None, client: httpx.AsyncClient | None = None):
        self.settings = settings or get_settings()
        self._client = client

    # --- configuration guards ---------------------------------------------
    @property
    def configured(self) -> bool:
        return bool(
            self.settings.google_client_id and self.settings.google_client_secret
        )

    def _require_configured(self) -> None:
        if not self.configured:
            raise OAuthError(
                "Google OAuth is not configured. Set GOOGLE_CLIENT_ID and "
                "GOOGLE_CLIENT_SECRET in backend/.env (create them at "
                "https://console.cloud.google.com/apis/credentials with the "
                "Gmail API enabled and redirect URI "
                f"{self.settings.google_redirect_uri})."
            )

    # --- authorization request ---------------------------------------------
    def make_state(self) -> str:
        return secrets.token_urlsafe(32)

    def build_authorize_url(self, state: str) -> str:
        self._require_configured()
        params = {
            "client_id": self.settings.google_client_id,
            "redirect_uri": self.settings.google_redirect_uri,
            "response_type": "code",
            "scope": " ".join(READONLY_GMAIL_SCOPES),
            "state": state,
            "access_type": "offline",       # request a refresh token
            "prompt": "consent",            # ensure refresh_token is returned
            "include_granted_scopes": "true",
        }
        return f"{self.settings.google_auth_uri}?{urlencode(params)}"

    @staticmethod
    def validate_state(expected: str | None, received: str | None) -> None:
        if not expected or not received or not secrets.compare_digest(expected, received):
            raise OAuthError(
                "OAuth state validation failed (possible CSRF). "
                "Please start the connection again."
            )

    # --- code exchange ------------------------------------------------------
    async def exchange_code(self, code: str) -> TokenBundle:
        self._require_configured()
        data = {
            "code": code,
            "client_id": self.settings.google_client_id,
            "client_secret": self.settings.google_client_secret,
            "redirect_uri": self.settings.google_redirect_uri,
            "grant_type": "authorization_code",
        }
        return await self._token_request(data)

    async def refresh_access_token(self, refresh_token: str) -> TokenBundle:
        self._require_configured()
        data = {
            "client_id": self.settings.google_client_id,
            "client_secret": self.settings.google_client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }
        bundle = await self._token_request(data)
        # Google usually omits refresh_token on refresh; keep the old one.
        if not bundle.refresh_token:
            bundle.refresh_token = refresh_token
        return bundle

    async def _token_request(self, data: dict) -> TokenBundle:
        try:
            async with self._new_client() as client:
                resp = await client.post(
                    self.settings.google_token_uri,
                    data=data,
                    headers={"Accept": "application/json"},
                )
        except httpx.HTTPError as exc:
            logger.error("Google token endpoint unreachable: %s", type(exc).__name__)
            raise OAuthError("Could not reach Google's token endpoint.") from exc

        payload = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
        if resp.status_code != 200:
            # Log the OAuth error code only — never the code/tokens themselves.
            error = payload.get("error", f"http_{resp.status_code}")
            logger.warning("Google token exchange failed: %s", error)
            raise OAuthError(f"Google rejected the request: {error}")

        access_token = payload.get("access_token")
        if not access_token:
            raise OAuthError("Google returned no access token.")
        return TokenBundle(
            access_token=access_token,
            refresh_token=payload.get("refresh_token"),
            expires_in=payload.get("expires_in"),
            scope=payload.get("scope", ""),
            token_type=payload.get("token_type", "Bearer"),
        )

    # --- identity -----------------------------------------------------------
    async def fetch_userinfo(self, access_token: str) -> dict:
        """Return {email, name, picture} for the authorized account."""
        try:
            async with self._new_client() as client:
                resp = await client.get(
                    self.settings.google_userinfo_uri,
                    headers={"Authorization": f"Bearer {access_token}"},
                )
            if resp.status_code == 200:
                return resp.json()
        except httpx.HTTPError:
            pass
        logger.warning("userinfo lookup failed; identity will be unknown")
        return {}

    def _new_client(self) -> httpx.AsyncClient:
        if self._client is not None:
            return _ReusingClient(self._client)
        return httpx.AsyncClient(timeout=20)


class _ReusingClient:
    """Context manager wrapper so an injected test client works with `async with`."""

    def __init__(self, client: httpx.AsyncClient):
        self._client = client

    async def __aenter__(self) -> httpx.AsyncClient:
        return self._client

    async def __aexit__(self, *args) -> None:
        return None
