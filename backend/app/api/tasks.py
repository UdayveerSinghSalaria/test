from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import date
import uuid

from app.database import get_db
from app.models.task import Task, TaskStatus, TaskPriority
from app.models.project import Project
from app.models.activity import Activity
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse
from app.dependencies import get_current_user, get_db_session
from app.models.user import User

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get("", response_model=List[TaskResponse])
async def get_tasks(
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    project: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Get all tasks with optional filters."""
    query = select(Task).where(Task.user_id == current_user.id).order_by(Task.due)

    if status and status != "All":
        try:
            query = query.where(Task.status == TaskStatus(status))
        except ValueError:
            pass

    if priority and priority != "All":
        try:
            query = query.where(Task.priority == TaskPriority(priority))
        except ValueError:
            pass

    if project and project != "All":
        query = query.where(Task.project == project)

    result = await db.execute(query)
    tasks = result.scalars().all()
    return [TaskResponse(**t.to_dict()) for t in tasks]


@router.post("", response_model=TaskResponse, status_code=201)
async def create_task(
    task_data: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Create a new task."""
    # Ensure project exists
    proj_result = await db.execute(select(Project).where(Project.name == task_data.project, Project.user_id == current_user.id))
    project = proj_result.scalars().first()
    if not project:
        project = Project(id=f"p-{uuid.uuid4().hex[:12]}", user_id=current_user.id, name=task_data.project)
        db.add(project)

    task = Task(
        id=f"t-{uuid.uuid4().hex[:12]}",
        user_id=current_user.id,
        title=task_data.title,
        project=task_data.project,
        priority=TaskPriority(task_data.priority),
        status=TaskStatus(task_data.status),
        due=task_data.due,
    )
    db.add(task)

    # Log activity
    activity = Activity(
        id=f"act-{uuid.uuid4().hex[:12]}",
        user_id=current_user.id,
        type="Task",
        title=f"Task created: {task.title}",
        detail=f"{task.project} · due {task.due}",
        source="My Space",
        status="Completed",
    )
    db.add(activity)

    await db.commit()
    await db.refresh(task)
    return TaskResponse(**task.to_dict())


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: str,
    patch: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Update a task."""
    result = await db.execute(select(Task).where(Task.id == task_id, Task.user_id == current_user.id))
    task = result.scalars().first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    update_data = patch.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "priority" and value:
            setattr(task, field, TaskPriority(value))
        elif field == "status" and value:
            setattr(task, field, TaskStatus(value))
        else:
            setattr(task, field, value)

    await db.commit()
    await db.refresh(task)
    return TaskResponse(**task.to_dict())


@router.delete("/{task_id}")
async def delete_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Delete a task."""
    result = await db.execute(select(Task).where(Task.id == task_id, Task.user_id == current_user.id))
    task = result.scalars().first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    title = task.title
    await db.delete(task)

    # Log activity
    activity = Activity(
        id=f"act-{uuid.uuid4().hex[:12]}",
        user_id=current_user.id,
        type="Task",
        title=f"Task deleted: {title}",
        detail="Removed from workspace",
        source="My Space",
        status="Completed",
    )
    db.add(activity)

    await db.commit()
    return {"message": "Task deleted", "task": {"id": task_id}}


@router.post("/{task_id}/toggle", response_model=TaskResponse)
async def toggle_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Toggle task status between todo and done."""
    result = await db.execute(select(Task).where(Task.id == task_id, Task.user_id == current_user.id))
    task = result.scalars().first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    new_status = TaskStatus.DONE if task.status == TaskStatus.TODO else TaskStatus.TODO
    task.status = new_status

    await db.commit()
    await db.refresh(task)
    return TaskResponse(**task.to_dict())