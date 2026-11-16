from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List

from app.database import get_db
from app.services.agent import AgentService
from app.models.agent_run import AgentRun
from app.schemas.agent import PlanRequest, PlanResponse, AgentRunResponse
from app.dependencies import get_current_user, get_db_session
from app.models.user import User

router = APIRouter(prefix="/agent", tags=["Agent"])


@router.post("/plan", response_model=PlanResponse)
async def generate_plan(
    request: PlanRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Generate an action plan using Nemotron AI."""
    agent_service = AgentService(db)
    try:
        result = await agent_service.generate_plan(
            command=request.command,
            webpage_url=request.webpageUrl,
            webpage_text=request.webpageText,
            current_user=current_user,
        )
        return PlanResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Plan generation failed: {str(e)}")


@router.get("/runs", response_model=List[AgentRunResponse])
async def get_agent_runs(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Get all agent runs."""
    result = await db.execute(select(AgentRun).where(AgentRun.user_id == current_user.id).order_by(desc(AgentRun.created_at)))
    runs = result.scalars().all()
    return [AgentRunResponse(**r.to_dict()) for r in runs]