from app.api.health import router as health_router
from app.api.tasks import router as tasks_router
from app.api.projects import router as projects_router
from app.api.agent import router as agent_router
from app.api.approvals import router as approvals_router
from app.api.activity import router as activity_router
from app.api.analytics import router as analytics_router
from app.api.settings import router as settings_router
from app.api.email import router as email_router
from app.api.auth import router as auth_router

__all__ = [
    "health_router",
    "tasks_router",
    "projects_router",
    "agent_router",
    "approvals_router",
    "activity_router",
    "analytics_router",
    "settings_router",
    "email_router",
    "auth_router",
]