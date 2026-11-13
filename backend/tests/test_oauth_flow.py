"""OAuth endpoint tests: connect redirect, state CSRF, callback, disconnect.

Google's endpoints are mocked; these tests verify OUR flow mechanics.
"""

from __future__ import annotations

from urllib.parse import parse_qs, urlparse

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.services.google_oauth import TokenBundle

SETTINGS = get_settings()


@pytest.fixture()
def configured(monkeypatch):
    """Temporarily provide dummy Google credentials."""
    monkeypatch.setattr(SETTINGS, "google_client_id", "dummy-client-id")
    monkeypatch.setattr(SETTINGS, "google_client_secret", "dummy-secret")
    yield
    # monkeypatch auto-reverts


@pytest.fixture()
def signed_in(client: TestClient):
    r = client.post(
        "/api/auth/signup",
        json={"email": "oauth-user@test.dev", "password": "password123"},
    )
    if r.status_code == 409:
        r = client.post(
            "/api/auth/login",
            json={"email": "oauth-user@test.dev", "password": "password123"},
        )
    assert r.status_code in (200, 201)
    return client


def test_connect_redirects_to_google(signed_in: TestClient, configured):
    r = signed_in.get("/api/integrations/google/connect", follow_redirects=False)
    assert r.status_code == 302
    loc = urlparse(r.headers["location"])
    assert loc.netloc == "accounts.google.com"
    qs = parse_qs(loc.query)
    assert qs["client_id"] == ["dummy-client-id"]
    assert qs["access_type"] == ["offline"]
    assert "gmail.readonly" in qs["scope"][0]
    state = qs["state"][0]
    # CSRF state must come back as an httpOnly cookie
    assert "awa_oauth_state" in r.cookies
    assert r.cookies["awa_oauth_state"] == state
    set_cookie = r.headers.get("set-cookie", "").lower()
    assert "httponly" in set_cookie


def test_connect_requires_auth(client: TestClient, configured):
    r = client.get("/api/integrations/google/connect", follow_redirects=False)
    assert r.status_code == 401


def test_callback_rejects_bad_state(signed_in: TestClient, configured):
    """State mismatch -> redirected to error, nothing stored."""
    r = signed_in.get(
        "/api/integrations/google/callback",
        params={"code": "abc", "state": "forged-state"},
        follow_redirects=False,
    )
    assert r.status_code == 302
    assert "status=error" in r.headers["location"]
    assert signed_in.get("/api/integrations/google/status").json() is None


def test_callback_missing_code(signed_in: TestClient, configured):
    r = signed_in.get(
        "/api/integrations/google/callback",
        params={"state": "x"},
        follow_redirects=False,
    )
    assert r.status_code == 302
    assert "status=error" in r.headers["location"]


def test_callback_google_error_param(signed_in: TestClient, configured):
    """User pressed Cancel on Google's screen."""
    r = signed_in.get(
        "/api/integrations/google/callback",
        params={"error": "access_denied", "state": "x"},
        follow_redirects=False,
    )
    assert r.status_code == 302
    assert "status=error" in r.headers["location"]


def test_full_callback_stores_encrypted_tokens(
    signed_in: TestClient, configured, monkeypatch
):
    """Happy path: valid state -> exchange -> encrypted storage -> success."""
    # 1. Start connect to obtain a valid state + cookie
    r = signed_in.get("/api/integrations/google/connect", follow_redirects=False)
    state = parse_qs(urlparse(r.headers["location"]).query)["state"][0]

    # 2. Mock the two Google calls
    async def fake_exchange(self, code: str) -> TokenBundle:
        assert code == "valid-code"
        return TokenBundle(
            access_token="live-access-token",
            refresh_token="live-refresh-token",
            expires_in=3600,
            scope="openid email profile gmail.readonly",
        )

    async def fake_userinfo(self, token: str) -> dict:
        assert token == "live-access-token"
        return {"email": "oauth-user@test.dev", "name": "OAuth User"}

    monkeypatch.setattr(
        "app.services.google_oauth.GoogleOAuthService.exchange_code",
        fake_exchange,
    )
    monkeypatch.setattr(
        "app.services.google_oauth.GoogleOAuthService.fetch_userinfo",
        fake_userinfo,
    )

    # 3. Callback
    r = signed_in.get(
        "/api/integrations/google/callback",
        params={"code": "valid-code", "state": state},
        follow_redirects=False,
    )
    assert r.status_code == 302
    assert "status=connected" in r.headers["location"]
    # state cookie consumed
    assert "awa_oauth_state" not in r.cookies or r.cookies.get("awa_oauth_state") == ""

    # 4. Status reflects the connection
    status = signed_in.get("/api/integrations/google/status").json()
    assert status is not None
    assert status["provider_email"] == "oauth-user@test.dev"
    assert "gmail.readonly" in " ".join(status["scopes"])

    # 5. Tokens are encrypted at rest — pull the raw row from the DB
    from app.database import SessionLocal
    from app.models import Integration, User
    from sqlalchemy import select

    db = SessionLocal()
    try:
        user = db.scalar(select(User).where(User.email == "oauth-user@test.dev"))
        row = db.scalar(select(Integration).where(Integration.user_id == user.id))
        assert row is not None
        assert "live-access-token" not in row.encrypted_access_token
        assert "live-refresh-token" not in row.encrypted_refresh_token
        # ...and decryptable with the backend key
        from app.security.encryption import decrypt

        assert decrypt(row.encrypted_access_token) == "live-access-token"
        assert decrypt(row.encrypted_refresh_token) == "live-refresh-token"
    finally:
        db.close()

    # 6. Disconnect removes it
    r = signed_in.delete("/api/integrations/google")
    assert r.status_code == 204
    assert signed_in.get("/api/integrations/google/status").json() is None

    # 7. Emails now report not-connected again
    assert signed_in.get("/api/emails").status_code == 409
