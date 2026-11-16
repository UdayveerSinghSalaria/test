from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.settings import Settings
from app.schemas.settings import SettingsResponse, SettingsUpdate
from app.dependencies import get_current_user, get_db_session
from app.models.user import User

router = APIRouter(prefix="/settings", tags=["Settings"])


@router.get("", response_model=SettingsResponse)
async def get_settings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Get user settings."""
    result = await db.execute(select(Settings).where(Settings.user_id == current_user.id))
    settings = result.scalars().first()

    if not settings:
        # Create default settings
        settings = Settings(user_id=current_user.id, data={})
        db.add(settings)
        await db.commit()
        await db.refresh(settings)

    return SettingsResponse(**settings.to_dict())


@router.post("", response_model=SettingsResponse)
async def save_settings(
    update: SettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Save user settings."""
    result = await db.execute(select(Settings).where(Settings.user_id == current_user.id))
    settings = result.scalars().first()

    if not settings:
        settings = Settings(user_id=current_user.id, data={})
        db.add(settings)

    settings.data = update.model_dump()
    await db.commit()
    await db.refresh(settings)
    return SettingsResponse(**settings.to_dict())