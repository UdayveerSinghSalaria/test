from sqlalchemy import Column, String, Text, DateTime, Index, ForeignKey
from sqlalchemy.sql import func

from app.database import Base


class Activity(Base):
    __tablename__ = "activity_logs"

    id = Column(String(64), primary_key=True)
    user_id = Column(String(64), ForeignKey("users.id"), nullable=False, index=True)
    type = Column(String(50), nullable=False)
    title = Column(String(500), nullable=False)
    detail = Column(Text, default="")
    source = Column(String(100), default="System")
    status = Column(String(50), default="Completed")
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (Index("ix_activity_timestamp", "timestamp"), Index("ix_activity_status", "status"), Index("ix_activity_user", "user_id"))

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "type": self.type,
            "title": self.title,
            "detail": self.detail,
            "source": self.source,
            "status": self.status,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "at": int(self.timestamp.timestamp() * 1000) if self.timestamp else None,
        }