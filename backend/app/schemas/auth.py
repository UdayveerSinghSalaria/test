from pydantic import BaseModel, Field, EmailStr
from typing import Optional, Literal


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    name: str = Field(..., min_length=1, max_length=100)
    email_provider: Literal["gmail", "yahoo", "outlook"]
    email_address: EmailStr
    email_app_password: str = Field(..., min_length=16)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str
    email_provider: Optional[str] = None
    email_address: Optional[str] = None
    has_email_configured: bool

    class Config:
        from_attributes = True


# Update forward references
Token.model_rebuild()