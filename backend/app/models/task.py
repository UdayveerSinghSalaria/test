from sqlalchemy import Column, String, Date, DateTime, Enum as SQLEnum, Index, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
import enum

from app.database import Base


class TaskStatus(str, enum.Enum):
    TODO = "todo"
    DOING = "doing"
    DONE = "done"


class TaskPriority(str, enum.Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class Task(Base):
    __tablename__ = "tasks"

    id = Column(String(64), primary_key=True, default=lambda: f"t-{uuid.uuid4().hex[:12]}")
    user_id = Column(String(64), ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    project = Column(String(100), default="General", nullable=False)
    priority = Column(SQLEnum(TaskPriority), default=TaskPriority.MEDIUM, nullable=False)
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.TODO, nullable=False)
    due = Column(Date, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index("ix_tasks_status", "status"),
        Index("ix_tasks_priority", "priority"),
        Index("ix_tasks_project", "project"),
        Index("ix_tasks_due", "due"),
        Index("ix_tasks_user", "user_id"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "project": self.project,
            "priority": self.priority.value,
            "status": self.status.value,
            "due": self.due.isoformat() if self.due else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }