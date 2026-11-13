"""Assistant API — runs the agent and streams step events to the browser.

Transport: newline-delimited JSON (NDJSON) over a streaming response, so the
UI can show plan -> tool calls -> approval prompts -> answer live without
waiting for the whole run.
"""

from __future__ import annotations

import json
import logging

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ..agents.orchestrator import run_agent
from ..database import get_db
from ..models import User
from ..schemas import AssistantRequest
from .deps import get_session_user

router = APIRouter(prefix="/api/assistant", tags=["assistant"])
logger = logging.getLogger(__name__)


@router.post("/run")
async def assistant_run(
    body: AssistantRequest,
    user: User = Depends(get_session_user),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    async def event_stream():
        try:
            async for step in run_agent(
                user_id=user.id, db_session=db, instruction=body.message
            ):
                yield json.dumps(step.model_dump(), default=str) + "\n"
        except Exception:
            logger.exception("assistant stream failed")
            yield json.dumps({"type": "error", "text": "Assistant run failed."}) + "\n"

    return StreamingResponse(
        event_stream(),
        media_type="application/x-ndjson",
        headers={
            "Cache-Control": "no-store",
            "X-Accel-Buffering": "no",
        },
    )
