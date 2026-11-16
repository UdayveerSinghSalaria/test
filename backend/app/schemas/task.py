from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import date


class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    project: str = Field(default="General", max_length=100)
    priority: Literal["High", "Medium", "Low"] = "Medium"
    status: Literal["todo", "doing", "done"] = "todo"
    due: date


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    project: Optional[str] = Field(None, max_length=100)
    priority: Optional[Literal["High", "Medium", "Low"]] = None
    status: Optional[Literal["todo", "doing", "done"]] = None
    due: Optional[date] = None


class TaskResponse(TaskBase):
    id: str
    created_at: str
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True