from pydantic import BaseModel
from typing import Optional


class HealthResponse(BaseModel):
    status: str
    app: str
    version: str
    database: str
    nemotronConfigured: bool
    port: int
    timestamp: str