from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import uuid

from app.database import get_db
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectResponse
from app.dependencies import get_current_user, get_db_session
from app.models.user import User

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get("", response_model=List[ProjectResponse])
async def get_projects(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Get all projects."""
    result = await db.execute(select(Project).where(Project.user_id == current_user.id).order_by(Project.name))
    projects = result.scalars().all()
    return [ProjectResponse(**p.to_dict()) for p in projects]


@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Create a new project."""
    # Check if exists for this user
    existing = await db.execute(select(Project).where(Project.name == project_data.name, Project.user_id == current_user.id))
    if existing.scalars().first():
        raise HTTPException(status_code=400, detail="Project already exists")

    project = Project(id=f"p-{uuid.uuid4().hex[:12]}", user_id=current_user.id, name=project_data.name)
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return ProjectResponse(**project.to_dict())