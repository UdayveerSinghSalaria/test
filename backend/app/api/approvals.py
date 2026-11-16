from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List, Optional

from app.database import get_db
from app.services.agent import AgentService
from app.models.proposal import Proposal, ProposalStatus
from app.schemas.proposal import ProposalResponse, ProposalUpdate, ApproveRequest, DecideResult
from app.dependencies import get_current_user, get_db_session
from app.models.user import User

router = APIRouter(prefix="/approvals", tags=["Approvals"])


@router.get("", response_model=List[ProposalResponse])
async def get_approvals(
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Get all proposals with optional status filter."""
    agent_service = AgentService(db)
    proposals = await agent_service.get_proposals(status, current_user)
    return [ProposalResponse(**p.to_dict()) for p in proposals]


@router.patch("/{proposal_id}", response_model=ProposalResponse)
async def update_proposal(
    proposal_id: str,
    patch: ProposalUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Update a proposal (e.g., edit tasks)."""
    agent_service = AgentService(db)
    proposal = await agent_service.update_proposal(proposal_id, patch.model_dump(exclude_unset=True), current_user)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    return ProposalResponse(**proposal.to_dict())


@router.post("/{proposal_id}/approve", response_model=DecideResult)
async def approve_proposal(
    proposal_id: str,
    request: ApproveRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Approve a proposal and execute the tasks."""
    agent_service = AgentService(db)
    try:
        result = await agent_service.decide_proposal(proposal_id, True, request.tasks, current_user)
        return DecideResult(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Approval failed: {str(e)}")


@router.post("/{proposal_id}/reject", response_model=DecideResult)
async def reject_proposal(
    proposal_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Reject a proposal."""
    agent_service = AgentService(db)
    try:
        result = await agent_service.decide_proposal(proposal_id, False, [], current_user)
        return DecideResult(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rejection failed: {str(e)}")