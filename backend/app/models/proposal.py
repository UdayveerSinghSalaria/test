from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, Text, Index, JSON, ForeignKey
from sqlalchemy.sql import func
import enum

from app.database import Base


class ProposalStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class Proposal(Base):
    __tablename__ = "proposals"

    id = Column(String(64), primary_key=True)
    user_id = Column(String(64), ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    source = Column(String(100), default="Agent Studio")
    url = Column(Text, default="")
    summary = Column(Text, default="")
    status = Column(SQLEnum(ProposalStatus), default=ProposalStatus.PENDING, nullable=False)
    tasks = Column(JSON, default=list, nullable=False)  # Array of proposal task objects
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    decided_at = Column(DateTime(timezone=True), nullable=True)
    execution_result = Column(JSON, nullable=True)  # {executed: bool, tasksCreated: int, reason: str}

    __table_args__ = (Index("ix_proposals_status", "status"), Index("ix_proposals_created", "created_at"), Index("ix_proposals_user", "user_id"))

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "source": self.source,
            "url": self.url,
            "summary": self.summary,
            "status": self.status.value,
            "tasks": self.tasks or [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "created": int(self.created_at.timestamp() * 1000) if self.created_at else None,
            "decided_at": self.decided_at.isoformat() if self.decided_at else None,
            "execution_result": self.execution_result,
        }