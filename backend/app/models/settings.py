from sqlalchemy import Column, String, DateTime, JSON, ForeignKey, Index
from sqlalchemy.sql import func

from app.database import Base


class Settings(Base):
    __tablename__ = "app_settings"

    id = Column(String(64), primary_key=True, default="default")
    user_id = Column(String(64), ForeignKey("users.id"), nullable=False, index=True, unique=True)
    data = Column(JSON, default=dict, nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (Index("ix_settings_user", "user_id"),)

    def to_dict(self):
        default_settings = {
            "name": "Riya",
            "email": "riya@example.com",
            "role": "Student Developer",
            "weekStart": "Mon",
            "notify": True,
            "demo": False,
            "emailProvider": "",
            "emailAddress": "",
            "emailAppPassword": "",
        }
        return {**default_settings, **(self.data or {})}