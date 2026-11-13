"""Authentication: email + password signup/login/logout/session."""

from __future__ import annotations

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, VerifyMismatchError
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..schemas import LoginRequest, SignupRequest, UserOut
from ..security.sessions import COOKIE_NAME, create_session_token, session_cookie_kwargs
from .deps import get_session_user

router = APIRouter(prefix="/api/auth", tags=["auth"])

hasher = PasswordHasher()


def _set_cookie(response: Response, user_id: str) -> None:
    token = create_session_token(user_id)
    response.set_cookie(COOKIE_NAME, token, **session_cookie_kwargs())


@router.post("/signup", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def signup(body: SignupRequest, response: Response, db: Session = Depends(get_db)) -> User:
    email = body.email.lower().strip()
    existing = db.scalar(select(User).where(User.email == email))
    if existing:
        raise HTTPException(status_code=409, detail="An account with this email already exists")
    user = User(
        email=email,
        name=body.name.strip() or email.split("@")[0],
        password_hash=hasher.hash(body.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    _set_cookie(response, user.id)
    return user


@router.post("/login", response_model=UserOut)
def login(body: LoginRequest, response: Response, db: Session = Depends(get_db)) -> User:
    email = body.email.lower().strip()
    user = db.scalar(select(User).where(User.email == email))
    # Constant failure message: never reveal whether the email exists.
    if user is None or not user.password_hash:
        hasher.hash(body.password)  # equalize timing
        raise HTTPException(status_code=401, detail="Invalid email or password")
    try:
        hasher.verify(user.password_hash, body.password)
    except (VerifyMismatchError, VerificationError):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if hasher.check_needs_rehash(user.password_hash):
        user.password_hash = hasher.hash(body.password)
        db.commit()
    _set_cookie(response, user.id)
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response) -> Response:
    # Mutate and return the SAME response so the cookie deletion ships.
    response.delete_cookie(COOKIE_NAME, path="/")
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_session_user)) -> User:
    return user
