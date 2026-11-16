from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List

from app.database import get_db
from app.models.task import Task, TaskStatus, TaskPriority
from app.models.activity import Activity
from app.models.proposal import Proposal, ProposalStatus
from app.schemas.analytics import AnalyticsResponse, PriorityDistribution, ProjectProgress
from app.dependencies import get_current_user, get_db_session
from app.models.user import User

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("", response_model=AnalyticsResponse)
async def get_analytics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Get computed analytics from database."""
    # Tasks
    tasks_result = await db.execute(select(Task).where(Task.user_id == current_user.id))
    tasks = tasks_result.scalars().all()

    total = len(tasks)
    done = len([t for t in tasks if t.status == TaskStatus.DONE])
    active = total - done
    rate = round((done / total) * 100) if total > 0 else 0

    # Priority distribution
    priority_counts = {"High": 0, "Medium": 0, "Low": 0}
    for t in tasks:
        if t.priority.value in priority_counts:
            priority_counts[t.priority.value] += 1

    priority_dist = [
        PriorityDistribution(name=k, value=v)
        for k, v in priority_counts.items()
    ]

    # Project progress
    project_stats = {}
    for t in tasks:
        proj = t.project or "General"
        if proj not in project_stats:
            project_stats[proj] = {"total": 0, "done": 0}
        project_stats[proj]["total"] += 1
        if t.status == TaskStatus.DONE:
            project_stats[proj]["done"] += 1

    project_progress = [
        ProjectProgress(
            name=name,
            total=stats["total"],
            done=stats["done"],
            pct=round((stats["done"] / stats["total"]) * 100) if stats["total"] > 0 else 0,
        )
        for name, stats in project_stats.items()
    ]

    # Activity
    activity_result = await db.execute(select(Activity).where(Activity.user_id == current_user.id))
    activity = activity_result.scalars().all()

    # Proposals
    proposals_result = await db.execute(select(Proposal).where(Proposal.user_id == current_user.id))
    proposals = proposals_result.scalars().all()

    return AnalyticsResponse(
        totalTasks=total,
        completedTasks=done,
        activeTasks=active,
        completionRate=rate,
        priorityDistribution=priority_dist,
        projectProgress=project_progress,
        totalActivity=len(activity),
        totalProposals=len(proposals),
        pendingProposals=len([p for p in proposals if p.status == ProposalStatus.PENDING]),
    )