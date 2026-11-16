from sqlalchemy import Column, String, Text, DateTime, Enum as SQLEnum, ForeignKey, Index
from sqlalchemy.sql import func
import enum

from app.database import Base


class AgentRunStatus(str, enum.Enum):
    PLANNED = "planned"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id = Column(String(64), primary_key=True)
    user_id = Column(String(64), ForeignKey("users.id"), nullable=False, index=True)
    command = Column(Text, nullable=False)
    status = Column(SQLEnum(AgentRunStatus), default=AgentRunStatus.COMPLETED)
    raw_input = Column(Text, default="")
    output_summary = Column(Text, default="")
    proposal_id = Column(String(64), ForeignKey("proposals.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (Index("ix_agent_runs_created", "created_at"), Index("ix_agent_runs_user", "user_id"))

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "command": self.command,
            "status": self.status.value,
            "raw_input": self.raw_input,
            "output_summary": self.output_summary,
            "proposal_id": self.proposal_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }