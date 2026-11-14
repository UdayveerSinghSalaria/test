"""AI Planner — converts a user instruction into a structured execution plan.

Uses the configured LLM provider with a structured-output contract enforced
by Pydantic. Falls back to a deterministic heuristic plan when no LLM is
configured, so the pipeline remains testable without keys (clearly marked).
"""

from __future__ import annotations

import json
import logging
import re
from typing import Literal

from pydantic import BaseModel, Field

from ..config import get_settings

logger = logging.getLogger(__name__)


class PlanStep(BaseModel):
    step: int = Field(ge=1, le=20)
    tool: str = Field(description="Tool name from the registry, or 'respond' for a direct answer.")
    reasoning: str = Field(default="", max_length=300)
    arguments: dict = Field(default_factory=dict)


class ExecutionPlan(BaseModel):
    """Structured output contract for the planner."""

    intent: str = Field(max_length=200, description="One-line restatement of the user's goal.")
    steps: list[PlanStep] = Field(min_length=1, max_length=10)
    needs_gmail: bool = False
    writes_data: bool = Field(
        default=False,
        description="True if the plan creates/modifies data (requires approval).",
    )


PLANNER_SYSTEM = """You are the planning module of a personal work assistant.
Given the user's instruction, produce a plan that uses ONLY these tools:
- search_emails: search mail; set include_body=true when the user asks to read, summarize, or analyze messages
- fetch_email: read one email by id
- list_tasks: list the user's tasks
- create_task: create a task (requires user approval)
- send_email: send an email (requires user approval of the exact recipient, subject, and body)
- respond: answer directly with no tool use

Rules:
- Prefer search_emails over fetching blindly.
- For a request to read or summarize matching emails, search with include_body=true.
- For a request to draft a reply to an existing email, search with include_body=true, then provide the complete draft in the answer; do not write to the mailbox.
- For a request to draft a new email without existing-message context, use respond and include the complete draft in the answer; do not write to the mailbox.
- If sending details are missing, use respond to ask for them instead of inventing them.
- Set needs_gmail true if any step touches email.
- Set writes_data true if any step calls create_task or send_email.
- Keep steps minimal: 1-4 steps for most requests.
Return ONLY JSON matching this schema:
{"intent": str, "steps": [{"step": int, "tool": str, "reasoning": str, "arguments": {}}], "needs_gmail": bool, "writes_data": bool}
"""

# Simple keyword heuristics — used only when no LLM is configured.
_KEYWORD_MAP = [
    (r"\b(deadline|due|when is|by \w+day)\b", "search_emails", {"query": "newer_than:30d"}),
    (r"\b(email|inbox|message|mail|from:)\b", "search_emails", {"query": "in:inbox"}),
    (r"\b(task|todo|to-do|remind)\b", "list_tasks", {}),
    (r"\b(unread|unread emails)\b", "search_emails", {"query": "is:unread"}),
]


def _heuristic_plan(instruction: str) -> ExecutionPlan:
    text = instruction.lower()
    steps: list[PlanStep] = []
    matched = False
    for pattern, tool, args in _KEYWORD_MAP:
        if re.search(pattern, text):
            steps.append(PlanStep(step=len(steps) + 1, tool=tool, arguments=dict(args),
                                  reasoning=f"matched keyword pattern /{pattern}/"))
            matched = True
            if len(steps) >= 2:
                break
    if not steps:
        steps.append(PlanStep(step=1, tool="respond", reasoning="No tool needed; answer directly."))
        matched = False
    needs_gmail = any(s.tool in {"search_emails", "fetch_email"} for s in steps)
    return ExecutionPlan(
        intent=instruction[:200],
        steps=steps,
        needs_gmail=needs_gmail,
        writes_data=any(s.tool == "create_task" for s in steps),
    )


async def make_plan(instruction: str, *, require_llm: bool = False) -> tuple[ExecutionPlan, str]:
    """Return (plan, mode). mode is 'llm' or 'heuristic'.

    With require_llm=True (the live agent path) a missing LLM config raises —
    we never silently pretend an LLM planned something.
    """
    settings = get_settings()
    if not settings.llm_configured:
        if require_llm:
            raise RuntimeError(
                "LLM is not configured. Set LLM_PROVIDER, LLM_BASE_URL, "
                "LLM_MODEL and LLM_API_KEY in backend/.env to enable the agent."
            )
        return _heuristic_plan(instruction), "heuristic"

    from .llm import chat_json

    messages = [
        {"role": "system", "content": PLANNER_SYSTEM},
        {"role": "user", "content": instruction},
    ]
    raw = await chat_json(messages)
    try:
        data = json.loads(raw) if isinstance(raw, str) else raw
        plan = ExecutionPlan.model_validate(data)
        return plan, "llm"
    except (json.JSONDecodeError, ValueError) as exc:
        logger.warning("Planner output not valid; retrying once. err=%s", type(exc).__name__)
        retry = await chat_json(messages, temperature=0)
        data = json.loads(retry) if isinstance(retry, str) else retry
        plan = ExecutionPlan.model_validate(data)
        return plan, "llm"
