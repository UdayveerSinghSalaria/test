"""Pydantic request/response schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# --- Auth -------------------------------------------------------------------
class SignupRequest(BaseModel):
    email: EmailStr
    name: str = Field(default="", max_length=255)
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    name: str
    created_at: datetime


# --- Integrations -----------------------------------------------------------
class IntegrationOut(BaseModel):
    provider: str
    provider_email: str
    scopes: list[str]
    connected_at: datetime
    token_expiry: datetime | None = None
    status: str = "connected"  # connected | error


# --- Emails -----------------------------------------------------------------
class EmailAddress(BaseModel):
    name: str = ""
    address: str = ""


class EmailSummary(BaseModel):
    id: str
    thread_id: str = ""
    sender_name: str = ""
    sender_email: str = ""
    subject: str = ""
    snippet: str = ""
    received_at: datetime | None = None
    is_unread: bool = False


class EmailListResponse(BaseModel):
    emails: list[EmailSummary]
    next_page_token: str | None = None


class EmailDetail(EmailSummary):
    to: list[EmailAddress] = []
    body_text: str = ""
    body_html_sanitized: str = ""
    label_ids: list[str] = []
    attachments: list[str] = []


# --- Tasks ------------------------------------------------------------------
class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    description: str = Field(default="", max_length=5000)
    priority: str = Field(default="medium")
    due_date: datetime | None = None
    source: str = Field(default="manual")


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=500)
    description: str | None = Field(default=None, max_length=5000)
    status: str | None = None
    priority: str | None = None
    due_date: datetime | None = None


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    description: str
    status: str
    priority: str
    due_date: datetime | None
    source: str
    created_at: datetime


# --- Approvals / activity ---------------------------------------------------
class ApprovalOut(BaseModel):
    id: str
    action: str
    payload: dict
    status: str
    created_at: datetime


class ActivityOut(BaseModel):
    id: str
    kind: str
    action: str
    status: str
    detail: str
    created_at: datetime


# --- Agent ------------------------------------------------------------------
class AssistantRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    run_id: str | None = None


class AgentStep(BaseModel):
    """One streamed event from the agent run."""

    type: str  # plan | tool_start | tool_result | approval_required | answer | error
    text: str = ""
    tool: str = ""
    detail: str = ""
    approval_id: str | None = None
