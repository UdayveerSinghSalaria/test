from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import jwt
import bcrypt
import uuid

from app.config import settings
from app.models.user import User
from app.models.email_account import EmailAccount, EmailProvider
from app.services.encryption import encrypt
from app.services.imap_service import IMAPService


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    def hash_password(self, password: str) -> str:
        # bcrypt handles encoding internally
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def verify_password(self, plain: str, hashed: str) -> bool:
        return bcrypt.checkpw(plain.encode('utf-8'), hashed.encode('utf-8'))

    def create_token(self, user: User) -> str:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode = {"sub": user.id, "email": user.email, "exp": expire}
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    async def register(self, data) -> User:
        # Check if email exists
        existing = await self.db.execute(select(User).where(User.email == data.email))
        if existing.scalars().first():
            raise ValueError("Email already registered")

        # Create user
        user = User(
            id=f"u-{uuid.uuid4().hex[:12]}",
            email=data.email,
            password_hash=self.hash_password(data.password),
            name=data.name,
        )
        self.db.add(user)

        # Create email account linked to user
        imap_config = IMAPService.get_provider_config(data.email_provider)
        email_account = EmailAccount(
            id=f"ea-{uuid.uuid4().hex[:12]}",
            user_id=user.id,
            provider=EmailProvider(data.email_provider),
            email_address=data.email_address,
            app_password_encrypted=encrypt(data.email_app_password),
            imap_host=imap_config["imap_host"],
            imap_port=str(imap_config["imap_port"]),
            smtp_host=imap_config["smtp_host"],
            smtp_port=str(imap_config["smtp_port"]),
            is_active="true",
        )
        self.db.add(email_account)

        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def login(self, email: str, password: str) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalars().first()
        if not user or not user.is_active:
            return None
        if not self.verify_password(password, user.password_hash):
            return None
        return user

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalars().first()

    async def get_user_email_account(self, user_id: str) -> Optional[EmailAccount]:
        result = await self.db.execute(
            select(EmailAccount).where(
                EmailAccount.user_id == user_id,
                EmailAccount.is_active == "true"
            )
        )
        return result.scalars().first()