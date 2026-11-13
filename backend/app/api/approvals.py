"""Approvals API — the human-in-the-loop gate for agent actions."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..agents.tools import ToolContext, execute_tool
from ..database import get_db
from ..models import ActivityKind, Approval, ApprovalStatus, Task, User
from ..schemas import ApprovalOut
from .deps import get_session_user

router = APIRouter(prefix="/api/approvals", tags=["approvals"])

# Actions this API is allowed to execute after explicit user consent.
_EXECUTORS = {"create_task"}


@router.get("", response_model=list[ApprovalOut])
def list_approvals(
    status: str = "pending",
    user: User = Depends(get_session_user),
    db: Session = Depends(get_db),
) -> list[Approval]:
    stmt = select(Approval).where(Approval.user_id == user.id)
    if status != "all":
        try:
            stmt = stmt.where(Approval.status == ApprovalStatus(status))
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Unknown status '{status}'")
    return list(db.scalars(stmt.order_by(Approval.created_at.desc()).limit(100)))


async def _resolve(
    approval_id: str, decision: ApprovalStatus, user: User, db: Session
) -> Approval:
    approval = db.scalar(
        select(Approval).where(Approval.id == approval_id, Approval.user_id == user.id)
    )
    if approval is None:
        raise HTTPException(status_code=404, detail="Approval request not found.")
    if approval.status != ApprovalStatus.pending:
        raise HTTPException(status_code=409, detail="This request was already resolved.")

    approval.status = decision
    approval.resolved_at = datetime.utcnow()

    if decision == ApprovalStatus.approved and approval.action in _EXECUTORS:
        # Execute the approved action with an explicit approval flag.
        ctx = ToolContext(user_id=user.id, db=db, run_id=approval.run_id)
        payload = dict(approval.payload or {})
        if approval.action == "create_task":
            from ..models import TaskPriority

            due = payload.pop("due_date", None)
            task = Task(
                user_id=user.id,
                title=str(payload.get("title", "Untitled task"))[:500],
                description=str(payload.get("description", ""))[:5000],
                priority=TaskPriority(payload.get("priority", "medium")),
                source="agent",
            )
            if due:
                from datetime import datetime as _dt

                try:
                    task.due_date = _dt.fromisoformat(str(due).replace("Z", ""))
                except ValueError:
                    pass
            db.add(task)
            db.commit()
            db.refresh(task)
            from ..agents.tools import log_activity

            log_activity(
                ctx, action="create_task", status="approved",
                detail=f"approval={approval.id} task_id={task.id}",
                kind=ActivityKind.approval,
            )
    else:
        db.commit()
        from ..agents.tools import log_activity

        ctx = ToolContext(user_id=user.id, db=db, run_id=approval.run_id)
        log_activity(
            ctx, action=approval.action, status="rejected",
            detail=f"approval={approval.id}", kind=ActivityKind.approval,
        )
    db.refresh(approval)
    return approval


@router.post("/{approval_id}/approve", response_model=ApprovalOut)
async def approve(
    approval_id: str,
    user: User = Depends(get_session_user),
    db: Session = Depends(get_db),
) -> Approval:
    return await _resolve(approval_id, ApprovalStatus.approved, user, db)


@router.post("/{approval_id}/reject", response_model=ApprovalOut)
async def reject(
    approval_id: str,
    user: User = Depends(get_session_user),
    db: Session = Depends(get_db),
) -> Approval:
    return await _resolve(approval_id, ApprovalStatus.rejected, user, db)
