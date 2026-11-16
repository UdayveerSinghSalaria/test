from pydantic import BaseModel
from typing import Optional


class ActivityResponse(BaseModel):
    id: str
    type: str
    title: str
    detail: str
    source: str
    status: str
    timestamp: str
    at: int

    class Config:
        from_attributes = True