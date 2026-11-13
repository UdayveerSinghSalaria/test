"""Integrations API: Google OAuth connect / callback / status / disconnect.

Full Authorization Code Flow, executed entirely on the backend.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from ..config import get_settings
from ..database import get_db
from ..models import User
from ..schemas import IntegrationOut
from ..security.sessions import COOKIE_NAME
from ..services.google_oauth import STATE_COOKIE, STATE_MAX_AGE, GoogleOAuthService, OAuthError
from ..services.token_service import TokenService
from .deps import get_session_user

router = APIRouter(prefix="/api/integrations", tags=["integrations"])
logger = logging.getLogger(__name__)


def _services() -> tuple[GoogleOAuthService, TokenService]:
    return GoogleOAuthService(), TokenService()


# ---------------------------------------------------------------------------
# Connect: redirect the browser to Google's official consent screen
# ---------------------------------------------------------------------------
@router.get("/google/connect")
async def google_connect(
    request: Request,
    response: Response,
    user: User = Depends(get_session_user),
):
    oauth, _ = _services()
    try:
        state = oauth.make_state()
        url = oauth.build_authorize_url(state)
    except OAuthError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    # Signed state cookie: only our own browser round-trip can validate it.
    redirect = RedirectResponse(url=url, status_code=302)
    redirect.set_cookie(
        STATE_COOKIE,
        state,
        httponly=True,
        samesite="lax",
        secure=get_settings().is_production,
        max_age=STATE_MAX_AGE,
        path="/",
    )
    logger.info("OAuth connect started for user %s", user.id)
    return redirect


# ---------------------------------------------------------------------------
# Callback: validate state, exchange code, store encrypted tokens
# ---------------------------------------------------------------------------
@router.get("/google/callback")
async def google_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    db: Session = Depends(get_db),
) -> RedirectResponse:
    settings = get_settings()
    frontend = settings.frontend_url.rstrip("/")
    oauth, tokens = _services()

    saved_state = request.cookies.get(STATE_COOKIE)

    def fail(message: str) -> RedirectResponse:
        r = RedirectResponse(f"{frontend}/integrations?status=error", status_code=302)
        r.delete_cookie(STATE_COOKIE, path="/")
        # Message travels in a flash cookie (short, non-sensitive) for the UI.
        r.set_cookie(
            "awa_flash",
            message[:200],
            httponly=True,
            samesite="lax",
            secure=settings.is_production,
            max_age=120,
            path="/",
        )
        return r

    # User pressed "Cancel" on Google's screen.
    if error:
        return fail(f"Google sign-in was cancelled ({error}).")

    if not code:
        return fail("Google did not return an authorization code.")

    # CSRF: state must match exactly what we issued to this browser.
    try:
        GoogleOAuthService.validate_state(saved_state, state)
    except OAuthError as exc:
        logger.warning("OAuth state validation failed")
        return fail(str(exc))

    # Resolve which app user this browser belongs to (from their session).
    from ..security.sessions import get_current_user

    session_token = request.cookies.get(COOKIE_NAME)
    app_user = get_current_user(session_token, db)
    if app_user is None:
        return fail("Your session expired. Sign in and connect Gmail again.")

    try:
        bundle = await oauth.exchange_code(code)
    except OAuthError as exc:
        return fail(str(exc))

    userinfo = await oauth.fetch_userinfo(bundle.access_token)
    provider_email = userinfo.get("email", "")

    tokens.upsert_integration(
        db,
        user_id=app_user.id,
        bundle=bundle,
        provider_email=provider_email,
    )
    logger.info("Gmail connected for user %s (%s)", app_user.id, provider_email or "email hidden")

    r = RedirectResponse(f"{frontend}/integrations?status=connected", status_code=302)
    r.delete_cookie(STATE_COOKIE, path="/")
    return r


# ---------------------------------------------------------------------------
# Status / disconnect
# ---------------------------------------------------------------------------
@router.get("/google/status", response_model=IntegrationOut | None)
async def google_status(
    user: User = Depends(get_session_user),
    db: Session = Depends(get_db),
):
    _, tokens = _services()
    row = tokens.get_integration(db, user.id)
    if row is None:
        return None
    return IntegrationOut(
        provider=row.provider,
        provider_email=row.provider_email,
        scopes=row.scopes.split(),
        connected_at=row.connected_at,
        token_expiry=row.token_expiry,
    )


@router.delete("/google", status_code=204)
async def google_disconnect(
    user: User = Depends(get_session_user),
    db: Session = Depends(get_db),
) -> Response:
    _, tokens = _services()
    removed = tokens.disconnect(db, user.id)
    if not removed:
        raise HTTPException(status_code=404, detail="Gmail is not connected.")
    logger.info("Gmail disconnected for user %s", user.id)
    return Response(status_code=204)


# ---------------------------------------------------------------------------
# Activepieces status (read-only; global/shared configuration)
# ---------------------------------------------------------------------------
@router.get("/activepieces/status", response_model=IntegrationOut | None)
async def activepieces_status(
    user: User = Depends(get_session_user),
):
    """Check if Activepieces mail is configured globally."""
    settings = get_settings()
    if not (settings.activepieces_api_key and settings.activepieces_search_flow_id):
        return None
    return IntegrationOut(
        provider="activepieces",
        provider_email="shared teammate mailbox (relan.toshan@gmail.com)",
        scopes=["gmail.readonly"],
        connected_at=None,
        token_expiry=None,
    )
