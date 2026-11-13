"""Tasks API: user-scoped CRUD (agent-created tasks land here too)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Task, TaskPriority, TaskStatus, User
from ..schemas import TaskCreate, TaskOut, TaskUpdate
from .deps import get_session_user

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

_STATUSES = {s.value for s in TaskStatus}
_PRIORITIES = {p.value for p in TaskPriority}


@router.get("", response_model=list[TaskOut])
def list_tasks(
    status: str | None = None,
    user: User = Depends(get_session_user),
    db: Session = Depends(get_db),
) -> list[Task]:
    stmt = select(Task).where(Task.user_id == user.id).order_by(Task.created_at.desc())
    if status:
        if status not in _STATUSES:
            raise HTTPException(status_code=400, detail=f"Unknown status '{status}'")
        stmt = stmt.where(Task.status == TaskStatus(status))
    return list(db.scalars(stmt))


@router.post("", response_model=TaskOut, status_code=201)
def create_task(
    body: TaskCreate,
    user: User = Depends(get_session_user),
    db: Session = Depends(get_db),
) -> Task:
    if body.priority not in _PRIORITIES:
        raise HTTPException(status_code=400, detail=f"Unknown priority '{body.priority}'")
    task = Task(
        user_id=user.id,
        title=body.title.strip(),
        description=body.description.strip(),
        priority=TaskPriority(body.priority),
        due_date=body.due_date,
        source=body.source,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.patch("/{task_id}", response_model=TaskOut)
def update_task(
    task_id: str,
    body: TaskUpdate,
    user: User = Depends(get_session_user),
    db: Session = Depends(get_db),
) -> Task:
    task = db.scalar(select(Task).where(Task.id == task_id, Task.user_id == user.id))
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found.")
    if body.status is not None:
        if body.status not in _STATUSES:
            raise HTTPException(status_code=400, detail=f"Unknown status '{body.status}'")
        task.status = TaskStatus(body.status)
    if body.priority is not None:
        if body.priority not in _PRIORITIES:
            raise HTTPException(status_code=400, detail=f"Unknown priority '{body.priority}'")
        task.priority = TaskPriority(body.priority)
    if body.title is not None:
        task.title = body.title.strip()
    if body.description is not None:
        task.description = body.description.strip()
    if body.due_date is not None:
        task.due_date = body.due_date
    db.commit()
    db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=204)
def delete_task(
    task_id: str,
    user: User = Depends(get_session_user),
    db: Session = Depends(get_db),
) -> None:
    task = db.scalar(select(Task).where(Task.id == task_id, Task.user_id == user.id))
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found.")
    db.delete(task)
    db.commit()
