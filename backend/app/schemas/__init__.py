from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse
from app.schemas.project import ProjectCreate, ProjectResponse
from app.schemas.proposal import ProposalCreate, ProposalUpdate, ProposalResponse, ProposalTask, ApproveRequest, DecideResult
from app.schemas.activity import ActivityResponse
from app.schemas.settings import SettingsResponse, SettingsUpdate
from app.schemas.analytics import AnalyticsResponse
from app.schemas.agent import PlanRequest, PlanResponse, AgentRunResponse
from app.schemas.email import EmailAccountCreate, EmailAccountResponse, EmailFetchRequest, EmailFetchResponse, EmailSendRequest, EmailSendResponse
from app.schemas.health import HealthResponse
from app.schemas.auth import UserRegister, UserLogin, Token, UserResponse

__all__ = [
    "TaskCreate", "TaskUpdate", "TaskResponse",
    "ProjectCreate", "ProjectResponse",
    "ProposalCreate", "ProposalUpdate", "ProposalResponse", "ProposalTask", "ApproveRequest", "DecideResult",
    "ActivityResponse",
    "SettingsResponse", "SettingsUpdate",
    "AnalyticsResponse",
    "PlanRequest", "PlanResponse", "AgentRunResponse",
    "EmailAccountCreate", "EmailAccountResponse", "EmailFetchRequest", "EmailFetchResponse", "EmailSendRequest", "EmailSendResponse",
    "HealthResponse",
    "UserRegister", "UserLogin", "Token", "UserResponse",
]