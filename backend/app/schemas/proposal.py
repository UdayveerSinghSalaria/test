from pydantic import BaseModel, Field
from typing import List, Optional, Any, Literal
from datetime import datetime


class ProposalTask(BaseModel):
    id: str
    title: str
    priority: Literal["High", "Medium", "Low"] = "Medium"
    due: str  # YYYY-MM-DD
    project: str = "General"
    actionType: str = "create_task"
    targetTaskId: Optional[str] = None


class ProposalBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    source: str = "Agent Studio"
    url: str = ""
    summary: str = ""
    tasks: List[ProposalTask] = []


class ProposalCreate(ProposalBase):
    pass


class ProposalUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    source: Optional[str] = None
    url: Optional[str] = None
    summary: Optional[str] = None
    tasks: Optional[List[ProposalTask]] = None
    status: Optional[Literal["pending", "approved", "rejected"]] = None


class ProposalResponse(ProposalBase):
    id: str
    status: Literal["pending", "approved", "rejected"]
    created_at: str
    created: int  # timestamp in ms
    decided_at: Optional[str] = None
    execution_result: Optional[dict] = None

    class Config:
        from_attributes = True


class ApproveRequest(BaseModel):
    tasks: List[ProposalTask] = []


class DecideResult(BaseModel):
    success: bool
    status: Literal["approved", "rejected"]
    proposalId: str
    createdTasks: List[dict] = []