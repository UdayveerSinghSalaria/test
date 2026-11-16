from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, Index
from sqlalchemy.sql import func
import enum

from app.database import Base


class EmailProvider(str, enum.Enum):
    GMAIL = "gmail"
    YAHOO = "yahoo"
    OUTLOOK = "outlook"


class EmailAccount(Base):
    __tablename__ = "email_accounts"

    id = Column(String(64), primary_key=True)
    user_id = Column(String(64), default="default", nullable=False)  # For future multi-user
    provider = Column(SQLEnum(EmailProvider), nullable=False)
    email_address = Column(String(255), nullable=False)
    # App password encrypted with Fernet
    app_password_encrypted = Column(String(500), nullable=False)
    imap_host = Column(String(255), nullable=False)
    imap_port = Column(String(10), default="993")
    smtp_host = Column(String(255), nullable=False)
    smtp_port = Column(String(10), default="587")
    is_active = Column(String(10), default="true")  # "true"/"false" for SQLite compat
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (Index("ix_email_accounts_user", "user_id"),)

    def to_dict(self, include_password: bool = False):
        d = {
            "id": self.id,
            "provider": self.provider.value,
            "email_address": self.email_address,
            "imap_host": self.imap_host,
            "imap_port": self.imap_port,
            "smtp_host": self.smtp_host,
            "smtp_port": self.smtp_port,
            "is_active": self.is_active == "true",
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_password:
            d["app_password_encrypted"] = self.app_password_encrypted
        return d