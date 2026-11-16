from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Literal


class EmailAccountCreate(BaseModel):
    provider: Literal["gmail", "yahoo", "outlook"]
    email_address: EmailStr
    app_password: str = Field(..., min_length=16, max_length=100)


class EmailAccountResponse(BaseModel):
    id: str
    provider: str
    email_address: str
    imap_host: str
    imap_port: str
    smtp_host: str
    smtp_port: str
    is_active: bool
    created_at: str

    class Config:
        from_attributes = True


class EmailFetchRequest(BaseModel):
    limit: int = Field(default=50, ge=1, le=200)
    since_days: int = Field(default=7, ge=1, le=90)
    folder: str = "INBOX"


class EmailItem(BaseModel):
    id: str
    subject: str
    from_: str = Field(alias="from")
    date: str
    body: str
    snippet: str

    class Config:
        populate_by_name = True


class EmailFetchResponse(BaseModel):
    emails: List[EmailItem]
    count: int


class EmailSendRequest(BaseModel):
    to: EmailStr
    subject: str = Field(..., min_length=1, max_length=200)
    body: str
    html_body: Optional[str] = None


class EmailSendResponse(BaseModel):
    success: bool
    message: str