"""Agent tool registry — predefined, permission-controlled tools.

The LLM never runs arbitrary code or SQL. It may only call these tools, each
of which is scoped to the requesting user and, where relevant, gated behind
the human approval engine.

Every tool takes a `ctx: ToolContext` (user, db, access-token provider) and
returns a plain dict suitable for the model's tool-result message.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Awaitable, Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Activity, ActivityKind, Approval, ApprovalStatus, Task, TaskPriority, TaskStatus
from ..services.gmail_service import GmailError, GmailService
from ..services.google_oauth import OAuthError
from ..services.token_service import TokenService

logger = logging.getLogger(__name__)

# Actions that MUST go through human approval before executing.
SENSITIVE_ACTIONS = {"create_task", "draft_email", "send_email", "create_calendar_event"}


@dataclass
class ToolContext:
    user_id: str
    db: Session
    run_id: str
    # Lazily resolved so tools work without Gmail connected for non-mail tools.
    token_provider: Callable[[], Awaitable[str]] | None = None
    # Filled by tools so the orchestrator can surface approval requests.
    pending_approvals: list[dict] = field(default_factory=list)


@dataclass
class ToolDef:
    name: str
    description: str
    parameters: dict[str, Any]  # JSON Schema
    sensitive: bool = False
    handler: Callable[..., Awaitable[dict]] = Callable  # type: ignore[assignment]


def log_activity(
    ctx: ToolContext, *, action: str, status: str = "ok", detail: str = "",
    kind: ActivityKind = ActivityKind.tool_call,
) -> None:
    """Audit logger. Detail must stay short and non-sensitive (no bodies)."""
    ctx.db.add(
        Activity(
            user_id=ctx.user_id,
            run_id=ctx.run_id,
            kind=kind,
            action=action,
            status=status,
            detail=detail[:500],
        )
    )
    ctx.db.commit()


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------
async def _require_token(ctx: ToolContext) -> str:
    if ctx.token_provider is None:
        raise OAuthError("Gmail is not connected. Connect your Google account first.")
    return await ctx.token_provider()


async def search_emails(ctx: ToolContext, *, query: str, max_results: int = 10) -> dict:
    """Search the Gmail inbox with Gmail search syntax (from:, is:unread, newer_than:7d...)."""
    token = await _require_token(ctx)
    try:
        results, _ = await GmailService().search(token, query, max_results=min(max_results, 25))
    except GmailError as exc:
        log_activity(ctx, action="search_emails", status="error", detail=str(exc))
        raise
    log_activity(ctx, action="search_emails", detail=f"q='{query[:80]}' n={len(results)}")
    return {
        "emails": [
            {
                "id": e.id,
                "from_name": e.sender_name,
                "from": e.sender_email,
                "subject": e.subject,
                "date": e.received_at.isoformat() if e.received_at else None,
                "snippet": e.snippet,
                "unread": e.is_unread,
            }
            for e in results
        ],
        "count": len(results),
    }


async def fetch_email(ctx: ToolContext, *, email_id: str) -> dict:
    """Fetch one email's full content (text preferred, HTML sanitized)."""
    if not email_id or len(email_id) > 128 or not all(c.isalnum() or c in "-_" for c in email_id):
        raise ValueError("Invalid email id.")
    token = await _require_token(ctx)
    try:
        detail = await GmailService().get_detail(token, email_id)
    except GmailError as exc:
        log_activity(ctx, action="fetch_email", status="error", detail=str(exc))
        raise
    log_activity(ctx, action="fetch_email", detail=f"id={email_id}")
    body = detail.body_text or _html_to_text(detail.body_html_sanitized)
    return {
        "id": detail.id,
        "from_name": detail.sender_name,
        "from": detail.sender_email,
        "to": [t.address for t in detail.to],
        "subject": detail.subject,
        "date": detail.received_at.isoformat() if detail.received_at else None,
        "body": body[:20_000],
        "attachments": detail.attachments,
    }


def _html_to_text(html: str) -> str:
    import re

    text = re.sub(r"<br\s*/?>", "\n", html, flags=re.I)
    text = re.sub(r"</(p|div|tr|li|h[1-6])>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    from html import unescape

    return unescape(text).strip()


async def list_tasks(
    ctx: ToolContext, *, status: str | None = None, limit: int = 20
) -> dict:
    """List the user's tasks (optionally filtered by status)."""
    stmt = (
        select(Task)
        .where(Task.user_id == ctx.user_id)
        .order_by(Task.created_at.desc())
        .limit(min(limit, 100))
    )
    if status:
        stmt = stmt.where(Task.status == TaskStatus(status))
    tasks = list(ctx.db.scalars(stmt))
    log_activity(ctx, action="list_tasks", detail=f"n={len(tasks)}")
    return {
        "tasks": [
            {
                "id": t.id,
                "title": t.title,
                "status": t.status.value,
                "priority": t.priority.value,
                "due_date": t.due_date.isoformat() if t.due_date else None,
                "source": t.source,
            }
            for t in tasks
        ],
        "count": len(tasks),
    }


async def create_task(
    ctx: ToolContext,
    *,
    title: str,
    description: str = "",
    priority: str = "medium",
    due_date: str | None = None,
    auto_approve: bool = False,
) -> dict:
    """Create a task. SENSITIVE: without prior approval it registers an
    approval request instead of writing."""
    title = (title or "").strip()
    if not title:
        raise ValueError("Task title is required.")
    if priority not in {p.value for p in TaskPriority}:
        priority = "medium"

    due: datetime | None = None
    if due_date:
        try:
            due = datetime.fromisoformat(due_date.replace("Z", ""))
        except ValueError:
            due = None

    if not auto_approve:
        approval = Approval(
            user_id=ctx.user_id,
            action="create_task",
            payload={
                "title": title[:500],
                "description": description[:2000],
                "priority": priority,
                "due_date": due.isoformat() if due else None,
            },
            run_id=ctx.run_id,
        )
        ctx.db.add(approval)
        ctx.db.commit()
        ctx.pending_approvals.append(
            {"approval_id": approval.id, "action": "create_task", "payload": approval.payload}
        )
        log_activity(
            ctx, action="create_task", status="pending_approval",
            detail=f"title='{title[:60]}'", kind=ActivityKind.approval,
        )
        return {
            "status": "approval_required",
            "approval_id": approval.id,
            "message": (
                "Creating a task changes your data, so it needs your approval. "
                "Tell the user an approval request is waiting on the Approvals page."
            ),
        }

    task = Task(
        user_id=ctx.user_id,
        title=title[:500],
        description=description[:5000],
        priority=TaskPriority(priority),
        due_date=due,
        source="agent",
    )
    ctx.db.add(task)
    ctx.db.commit()
    ctx.db.refresh(task)
    log_activity(ctx, action="create_task", detail=f"task_id={task.id} title='{title[:60]}'")
    return {"status": "created", "task_id": task.id, "title": task.title}


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------
TOOL_HANDLERS: dict[str, Callable[..., Awaitable[dict]]] = {
    "search_emails": search_emails,
    "fetch_email": fetch_email,
    "list_tasks": list_tasks,
    "create_task": create_task,
}

TOOL_DEFS: list[dict[str, Any]] = [
    {
        "name": "search_emails",
        "description": (
            "Search the user's Gmail inbox using Gmail search syntax "
            "(e.g. 'from:alice@x.com', 'is:unread', 'subject:invoice', 'newer_than:7d'). "
            "Returns matching messages with sender, subject, date and snippet."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Gmail search query."},
                "max_results": {"type": "integer", "description": "1-25, default 10."},
            },
            "required": ["query"],
        },
        "sensitive": False,
    },
    {
        "name": "fetch_email",
        "description": (
            "Fetch the full content of one email by its id (from search_emails results). "
            "Returns decoded text body; HTML is sanitized."
        ),
        "parameters": {
            "type": "object",
            "properties": {"email_id": {"type": "string", "description": "Gmail message id."}},
            "required": ["email_id"],
        },
        "sensitive": False,
    },
    {
        "name": "list_tasks",
        "description": "List the user's tasks, optionally filtered by status (pending|in_progress|completed).",
        "parameters": {
            "type": "object",
            "properties": {
                "status": {"type": "string", "enum": ["pending", "in_progress", "completed"]},
                "limit": {"type": "integer", "description": "Max results, default 20."},
            },
        },
        "sensitive": False,
    },
    {
        "name": "create_task",
        "description": (
            "Create a task in the user's task list. Requires explicit user approval "
            "before it is actually created."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Short action title."},
                "description": {"type": "string", "description": "Details / context."},
                "priority": {"type": "string", "enum": ["low", "medium", "high"]},
                "due_date": {"type": "string", "description": "ISO date, e.g. 2026-11-20."},
            },
            "required": ["title"],
        },
        "sensitive": True,
    },
]


def tools_for_model() -> list[dict[str, Any]]:
    """Tool list in the OpenAI function-calling shape."""
    return [
        {"type": "function", "function": {"name": t["name"], "description": t["description"], "parameters": t["parameters"]}}
        for t in TOOL_DEFS
    ]


async def execute_tool(name: str, arguments: dict, ctx: ToolContext) -> dict:
    """Dispatch a model tool call. Unknown tools are refused, not improvised."""
    handler = TOOL_HANDLERS.get(name)
    if handler is None:
        log_activity(ctx, action=name, status="refused", detail="unknown tool", kind=ActivityKind.error)
        raise ValueError(f"Unknown tool: {name}")
    try:
        return await handler(ctx, **arguments)
    except (GmailError, OAuthError) as exc:
        return {"error": str(exc)}
    except TypeError as exc:
        return {"error": f"Invalid arguments for {name}: {exc}"}
    except ValueError as exc:
        return {"error": str(exc)}
