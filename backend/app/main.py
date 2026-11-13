"""FastAPI application entrypoint.

Security posture:
  * Fail-fast configuration validation (missing secrets refuse startup).
  * Strict CORS: only the configured frontend origin, credentials allowed.
  * Google OAuth and Gmail live entirely on this backend.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import get_settings
from .database import init_db
from .services.google_oauth import OAuthError

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.validate_security()  # refuses to run with missing/broken secrets
    init_db()
    logger.info(
        "%s started (env=%s, db=%s, llm=%s)",
        settings.app_name,
        settings.app_env,
        settings.database_url.split("://")[0],
        "configured" if settings.llm_configured else "not configured",
    )
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/api/docs" if not settings.is_production else None,
    openapi_url="/api/openapi.json" if not settings.is_production else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,  # session cookie is cross-origin (3000 -> 8000)
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type"],
    max_age=600,
)


@app.exception_handler(OAuthError)
async def oauth_error_handler(request: Request, exc: OAuthError) -> JSONResponse:
    """OAuth failures are user-facing but never leak internals."""
    return JSONResponse(status_code=409, content={"detail": str(exc)})


@app.get("/api/health")
def health() -> dict:
    return {
        "status": "ok",
        "app_name": settings.app_name,
        "llm_configured": settings.llm_configured,
        "google_oauth_configured": bool(
            settings.google_client_id and settings.google_client_secret
        ),
    }


@app.get("/health")
def health_root() -> dict:
    return {
        "status": "ok",
        "app_name": settings.app_name,
        "llm_configured": settings.llm_configured,
        "google_oauth_configured": bool(
            settings.google_client_id and settings.google_client_secret
        ),
    }


@app.get("/")
def root() -> dict:
    return {
        "name": settings.app_name,
        "version": "0.1.0",
        "docs": "/api/docs",
        "health": "/health",
    }


# --- routes -----------------------------------------------------------------
from .api import (  # noqa: E402  (routers need `app` defined)
    activity,
    approvals,
    assistant,
    auth,
    emails,
    integrations,
    tasks,
)

for router in (
    auth.router,
    integrations.router,
    emails.router,
    tasks.router,
    approvals.router,
    activity.router,
    assistant.router,
):
    app.include_router(router)
