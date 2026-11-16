from pydantic import BaseModel, Field
from typing import List, Optional
from app.schemas.proposal import ProposalTask


class PlanRequest(BaseModel):
    command: str = Field(..., min_length=1)
    webpageUrl: Optional[str] = None
    webpageText: Optional[str] = None


class PlanResponse(BaseModel):
    success: bool
    proposalId: str
    runId: str
    summary: str
    tasks: List[ProposalTask]
    isSimulated: bool
    warning: Optional[str] = None


class AgentRunResponse(BaseModel):
    id: str
    command: str
    status: str
    raw_input: str
    output_summary: str
    proposal_id: Optional[str] = None
    created_at: str

    class Config:
        from_attributes = True