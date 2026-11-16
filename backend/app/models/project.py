from sqlalchemy import Column, String, Index, ForeignKey
from app.database import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(String(64), primary_key=True)
    user_id = Column(String(64), ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)

    __table_args__ = (Index("ix_projects_name", "name"), Index("ix_projects_user", "user_id"),)

    def to_dict(self):
        return {"id": self.id, "user_id": self.user_id, "name": self.name}