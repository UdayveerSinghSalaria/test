from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List, Optional

from app.database import get_db
from app.models.activity import Activity
from app.schemas.activity import ActivityResponse
from app.dependencies import get_current_user, get_db_session
from app.models.user import User

router = APIRouter(prefix="/activity", tags=["Activity"])


@router.get("", response_model=List[ActivityResponse])
async def get_activity(
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Get activity logs with optional status filter."""
    query = select(Activity).where(Activity.user_id == current_user.id).order_by(desc(Activity.timestamp))
    if status and status != "All":
        query = query.where(Activity.status == status)

    result = await db.execute(query)
    activities = result.scalars().all()
    return [ActivityResponse(**a.to_dict()) for a in activities]