"""Shared FastAPI dependencies (auth guard, etc.)."""

from __future__ import annotations

from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..config import Settings, get_settings
from ..database import get_db
from ..models import User
from ..security.sessions import COOKIE_NAME, get_current_user


def get_session_user(
    db: Session = Depends(get_db),
    session: str | None = Cookie(default=None, alias=COOKIE_NAME),
) -> User:
    """Require an authenticated user; 401 otherwise.

    Every user-scoped endpoint depends on this, which is what enforces
    user-level data isolation together with per-query user_id filters.
    """
    user = get_current_user(session, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )
    return user


__all__ = ["get_session_user", "get_db", "get_settings", "Settings"]
