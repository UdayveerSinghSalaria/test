"""Session management: signed, httpOnly cookies (never localStorage).

Sessions carry only the user id; everything else is looked up server-side.
"""

from __future__ import annotations

from itsdangerous import BadSignature, URLSafeTimedSerializer
from sqlalchemy.orm import Session as DbSession

from ..config import get_settings
from ..models import User

COOKIE_NAME = "awa_session"

_serializer: URLSafeTimedSerializer | None = None


def _get_serializer() -> URLSafeTimedSerializer:
    global _serializer
    if _serializer is None:
        _serializer = URLSafeTimedSerializer(
            get_settings().session_secret, salt="awa-session"
        )
    return _serializer


def create_session_token(user_id: str) -> str:
    return _get_serializer().dumps({"uid": user_id})


def read_session_token(token: str) -> str | None:
    """Return the user id if the signature is valid and not expired."""
    try:
        data = _get_serializer().loads(token, max_age=get_settings().session_max_age)
    except BadSignature:
        return None
    uid = data.get("uid")
    return uid if isinstance(uid, str) else None


def session_cookie_kwargs() -> dict:
    """Cookie flags for setting/clearing the session cookie."""
    settings = get_settings()
    return {
        "httponly": True,
        "samesite": "lax",
        "secure": settings.is_production,
        "max_age": settings.session_max_age,
        "path": "/",
    }


def get_current_user(token: str | None, db: DbSession) -> User | None:
    """Resolve a session token to a live User row (or None)."""
    if not token:
        return None
    user_id = read_session_token(token)
    if not user_id:
        return None
    return db.get(User, user_id)
