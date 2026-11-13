"""Backend tests: auth, security, OAuth flow, email parsing, tools, APIs.

Google/LLM network calls are mocked with httpx transports — these tests
verify OUR logic, not Google's uptime. Live OAuth is tested manually with
real credentials (see README).
"""

from __future__ import annotations

import base64
from datetime import datetime, timedelta

import httpx
import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.security.encryption import decrypt, encrypt
from app.security.sessions import create_session_token, read_session_token
from app.services.gmail_service import GmailService, sanitize_html
from app.services.google_oauth import GoogleOAuthService, OAuthError

SETTINGS = get_settings()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture()
def auth_client(client: TestClient):
    """Client with a signed-in user session."""
    email = "tester@example.com"
    r = client.post(
        "/api/auth/signup",
        json={"email": email, "name": "Tester", "password": "password123"},
    )
    if r.status_code == 409:  # already exists from a prior run
        r = client.post(
            "/api/auth/login",
            json={"email": email, "password": "password123"},
        )
    assert r.status_code in (200, 201), r.text
    return client


# ---------------------------------------------------------------------------
# Security primitives
# ---------------------------------------------------------------------------
def test_encryption_roundtrip():
    secret = "ya29.a0AfH6SMB-secret-token"
    token = encrypt(secret)
    assert token != secret, "token must not be stored in plaintext"
    assert decrypt(token) == secret


def test_decrypt_tampered_fails():
    token = encrypt("hello")
    with pytest.raises(ValueError):
        decrypt(token[:-4] + "AAAA")


def test_session_roundtrip():
    token = create_session_token("user123")
    assert read_session_token(token) == "user123"


def test_session_tampered_rejected():
    token = create_session_token("user123")
    assert read_session_token(token + "x") is None


def test_security_config_valid():
    SETTINGS.validate_security()  # must not raise with .env present


# ---------------------------------------------------------------------------
# HTML sanitization (email content is untrusted)
# ---------------------------------------------------------------------------
def test_sanitize_removes_script():
    out = sanitize_html("<p>hi</p><script>alert('xss')</script>")
    assert "script" not in out.lower()
    assert "hi" in out


def test_sanitize_removes_event_handlers_and_js_urls():
    out = sanitize_html('<a href="javascript:alert(1)" onclick="evil()">x</a>')
    assert "javascript:" not in out
    assert "onclick" not in out


def test_sanitize_keeps_safe_markup():
    out = sanitize_html("<b>bold</b> <a href='https://example.com'>link</a>")
    assert "<b>bold</b>" in out
    assert 'href="https://example.com"' in out


def test_sanitize_escapes_raw_tags_in_data():
    out = sanitize_html("<div><img src=x onerror=alert(1)></div>")
    assert "onerror" not in out


# ---------------------------------------------------------------------------
# Multipart / body decoding
# ---------------------------------------------------------------------------
def _b64(data: str) -> str:
    return base64.urlsafe_b64encode(data.encode()).decode().rstrip("=")


def test_gmail_detail_multipart_alternative():
    """text/plain preferred over text/html in multipart/alternative."""
    plain = "Plain version of the email"
    html = "<html><body><p>HTML version</p></body></html>"
    message = {
        "id": "m1",
        "threadId": "t1",
        "labelIds": ["INBOX", "UNREAD"],
        "snippet": "Plain version...",
        "internalDate": "1765000000000",
        "payload": {
            "headers": [
                {"name": "From", "value": "Jane Doe <jane@example.com>"},
                {"name": "Subject", "value": "Quarterly report"},
                {"name": "To", "value": "me@example.com"},
            ],
            "parts": [
                {
                    "mimeType": "text/plain",
                    "body": {"data": _b64(plain), "size": len(plain)},
                },
                {
                    "mimeType": "text/html",
                    "body": {"data": _b64(html), "size": len(html)},
                },
            ],
        },
    }

    captured = {}

    class StubTransport(httpx.AsyncBaseTransport):
        async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
            captured["url"] = str(request.url)
            return httpx.Response(200, json=message)

    svc = GmailService(client=httpx.AsyncClient(transport=StubTransport()))
    import asyncio

    detail = asyncio.run(svc.get_detail("token", "m1"))

    assert detail.sender_name == "Jane Doe"
    assert detail.sender_email == "jane@example.com"
    assert detail.subject == "Quarterly report"
    assert detail.body_text == plain
    assert "HTML version" in detail.body_html_sanitized
    assert detail.is_unread is True
    assert "/messages/m1" in captured["url"]


def test_gmail_list_maps_summaries():
    listing = {"messages": [{"id": "a"}, {"id": "b"}], "nextPageToken": "p2"}
    meta = {
        "id": "a",
        "labelIds": ["INBOX"],
        "internalDate": "1765000000000",
        "snippet": "hey",
        "payload": {
            "headers": [
                {"name": "From", "value": "Bob <bob@x.com>"},
                {"name": "Subject", "value": "Hello"},
            ]
        },
    }

    class StubTransport(httpx.AsyncBaseTransport):
        async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
            if "/messages?" in str(request.url) or str(request.url).endswith("/messages"):
                return httpx.Response(200, json=listing)
            return httpx.Response(200, json=meta)

    svc = GmailService(client=httpx.AsyncClient(transport=StubTransport()))
    import asyncio

    emails, token_out = asyncio.run(svc.list_latest("tok", max_results=5))
    assert token_out == "p2"
    assert len(emails) == 2  # stub returns same meta for both ids
    assert emails[0].sender_email == "bob@x.com"


def test_gmail_auth_error_maps_to_friendly():
    class StubTransport(httpx.AsyncBaseTransport):
        async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
            return httpx.Response(401, json={"error": "unauthorized"})

    svc = GmailService(client=httpx.AsyncClient(transport=StubTransport()))
    from app.services.gmail_service import GmailError

    import asyncio

    with pytest.raises(GmailError) as exc:
        asyncio.run(svc.list_latest("bad-token"))
    assert "Reconnect" in str(exc.value)


# ---------------------------------------------------------------------------
# OAuth flow
# ---------------------------------------------------------------------------
def test_authorize_url_contains_required_params():
    if not SETTINGS.google_client_id:
        pytest.skip("Google credentials not configured")
    svc = GoogleOAuthService()
    url = svc.build_authorize_url("state123")
    assert "accounts.google.com" in url
    assert "gmail.readonly" in url
    assert "access_type=offline" in url
    assert "state=state123" in url
    assert "client_secret" not in url, "secret must never appear in URLs"


def test_state_validation_rejects_mismatch():
    GoogleOAuthService.validate_state("abc", "abc")  # ok
    with pytest.raises(OAuthError):
        GoogleOAuthService.validate_state("abc", "xyz")
    with pytest.raises(OAuthError):
        GoogleOAuthService.validate_state(None, "abc")
    with pytest.raises(OAuthError):
        GoogleOAuthService.validate_state("abc", None)


def _oauth_settings():
    """Dummy creds: these tests mock Google's endpoint, not hit it."""
    from app.config import Settings

    return Settings(
        google_client_id="test-client-id",
        google_client_secret="test-secret",
    )


def test_token_exchange_success():
    class StubTransport(httpx.AsyncBaseTransport):
        async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                json={
                    "access_token": "at-123",
                    "refresh_token": "rt-456",
                    "expires_in": 3599,
                    "scope": "openid email profile",
                },
            )

    svc = GoogleOAuthService(
        settings=_oauth_settings(),
        client=httpx.AsyncClient(transport=StubTransport()),
    )
    import asyncio

    bundle = asyncio.run(svc.exchange_code("code"))
    assert bundle.access_token == "at-123"
    assert bundle.refresh_token == "rt-456"
    assert bundle.expiry_datetime is not None
    assert bundle.expiry_datetime < datetime.utcnow() + timedelta(hours=1)


def test_token_exchange_error_raises():
    class StubTransport(httpx.AsyncBaseTransport):
        async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
            return httpx.Response(400, json={"error": "invalid_grant"})

    svc = GoogleOAuthService(
        settings=_oauth_settings(),
        client=httpx.AsyncClient(transport=StubTransport()),
    )
    import asyncio

    with pytest.raises(OAuthError) as exc:
        asyncio.run(svc.exchange_code("bad"))
    assert "invalid_grant" in str(exc.value)


# ---------------------------------------------------------------------------
# API: auth + isolation
# ---------------------------------------------------------------------------
def test_signup_login_logout_me(client: TestClient):
    r = client.post(
        "/api/auth/signup",
        json={"email": "a@example.com", "password": "password123"},
    )
    assert r.status_code == 201

    r = client.get("/api/auth/me")
    assert r.status_code == 200
    assert r.json()["email"] == "a@example.com"

    # duplicate signup refused
    r = client.post(
        "/api/auth/signup",
        json={"email": "a@example.com", "password": "password123"},
    )
    assert r.status_code == 409

    r = client.post("/api/auth/logout")
    assert r.status_code == 204
    r = client.get("/api/auth/me")
    assert r.status_code == 401


def test_wrong_password_rejected(client: TestClient):
    client.post(
        "/api/auth/signup",
        json={"email": "b@example.com", "password": "password123"},
    )
    client.post("/api/auth/logout")
    r = client.post(
        "/api/auth/login",
        json={"email": "b@example.com", "password": "wrong-password"},
    )
    assert r.status_code == 401


def test_endpoints_require_auth(client: TestClient):
    for path in ("/api/emails", "/api/tasks", "/api/activity", "/api/approvals",
                 "/api/integrations/google/status"):
        assert client.get(path).status_code == 401, path


def test_emails_409_when_gmail_not_connected(auth_client: TestClient):
    r = auth_client.get("/api/emails")
    assert r.status_code == 409
    assert "not connected" in r.json()["detail"].lower()


# ---------------------------------------------------------------------------
# API: tasks + user isolation
# ---------------------------------------------------------------------------
def test_task_crud(auth_client: TestClient):
    r = auth_client.post("/api/tasks", json={"title": "Write report"})
    assert r.status_code == 201
    task_id = r.json()["id"]

    r = auth_client.get("/api/tasks")
    assert len(r.json()) == 1

    r = auth_client.patch(f"/api/tasks/{task_id}", json={"status": "completed"})
    assert r.json()["status"] == "completed"

    r = auth_client.delete(f"/api/tasks/{task_id}")
    assert r.status_code == 204
    assert auth_client.get("/api/tasks").json() == []


def test_task_validation(auth_client: TestClient):
    assert auth_client.post("/api/tasks", json={"title": ""}).status_code == 422
    r = auth_client.post(
        "/api/tasks", json={"title": "x", "priority": "urgent"}
    )
    assert r.status_code == 400


def test_user_isolation(client: TestClient):
    """User A cannot see user B's tasks."""
    client.post("/api/auth/signup",
                json={"email": "a@iso.com", "password": "password123"})
    client.post("/api/tasks", json={"title": "A private task"})
    client.post("/api/auth/logout")

    client.post("/api/auth/signup",
                json={"email": "b@iso.com", "password": "password123"})
    assert client.get("/api/tasks").json() == []


# ---------------------------------------------------------------------------
# Approval gate
# ---------------------------------------------------------------------------
def test_create_task_tool_requires_approval(auth_client: TestClient):
    """The agent's create_task must register an approval, not write directly."""
    import asyncio

    from app.agents.tools import ToolContext, execute_tool
    from app.database import get_db
    from app.models import Approval, User
    from sqlalchemy import select

    # Resolve the signed-in user id via session cookie
    me = auth_client.get("/api/auth/me").json()

    # Build a request-scoped DB session the same way routes do
    db = next(get_db())
    try:
        user = db.scalar(select(User).where(User.id == me["id"]))
        ctx = ToolContext(user_id=user.id, db=db, run_id="run-test")
        result = asyncio.run(
            execute_tool(
                "create_task",
                {"title": "Agent-created", "priority": "high"},
                ctx,
            )
        )
        assert result["status"] == "approval_required"
        approvals = list(db.scalars(select(Approval)))
        assert len(approvals) == 1
        assert approvals[0].action == "create_task"

        # Approve via the API — now the task exists
        approval_id = approvals[0].id
        r = auth_client.post(f"/api/approvals/{approval_id}/approve")
        assert r.status_code == 200
        assert r.json()["status"] == "approved"

        tasks = auth_client.get("/api/tasks").json()
        assert len(tasks) == 1
        assert tasks[0]["title"] == "Agent-created"
        assert tasks[0]["source"] == "agent"
    finally:
        db.close()


def test_unknown_tool_refused():
    import asyncio

    from app.agents.tools import ToolContext, execute_tool
    from app.database import get_db

    db = next(get_db())
    try:
        ctx = ToolContext(user_id="u", db=db, run_id="r")
        with pytest.raises(ValueError):
            asyncio.run(execute_tool("run_shell", {"cmd": "rm -rf /"}, ctx))
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Activity audit log
# ---------------------------------------------------------------------------
def test_activity_returns_own_rows_only(auth_client: TestClient):
    r = auth_client.get("/api/activity")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_health(client: TestClient):
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "llm_configured" in body
    assert "google_oauth_configured" in body
