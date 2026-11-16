from pydantic import BaseModel, Field, EmailStr
from typing import Optional, Literal


class SettingsBase(BaseModel):
    name: str = Field(default="Riya", max_length=100)
    email: EmailStr = "riya@example.com"
    role: str = Field(default="Student Developer", max_length=100)
    weekStart: Literal["Mon", "Sun"] = "Mon"
    notify: bool = True
    demo: bool = False
    emailProvider: Literal["", "gmail", "yahoo", "outlook"] = ""
    emailAddress: str = ""
    emailAppPassword: str = ""


class SettingsResponse(SettingsBase):
    class Config:
        from_attributes = True


class SettingsUpdate(SettingsBase):
    pass