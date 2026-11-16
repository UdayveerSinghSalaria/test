from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List, Optional
import os


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./saarthiflow.db"

    # NVIDIA Nemotron
    NVIDIA_API_KEY: str = ""
    NVIDIA_MODEL: str = "nvidia/nemotron-3-ultra-550b-a55b"
    NVIDIA_BASE_URL: str = "https://integrate.api.nvidia.com/v1"

    # SMTP (for sending emails)
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "SaarthiFlow <noreply@saarthiflow.com>"

    # IMAP defaults (per-user settings override these)
    IMAP_HOST: str = "imap.gmail.com"
    IMAP_PORT: int = 993

    # Activepieces (fallback)
    ACTIVEPIECES_API_KEY: str = ""
    ACTIVEPIECES_BASE_URL: str = "https://cloud.activepieces.com/api/v1"
    ACTIVEPIECES_SEARCH_FLOW_ID: str = ""
    ACTIVEPIECES_GET_FLOW_ID: str = ""

    # Security
    SECRET_KEY: str = Field(default="", min_length=32)
    FERNET_KEY: str = Field(default="", min_length=32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # CORS
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:5174,http://127.0.0.1:5173,http://127.0.0.1:5174"

    # Environment
    ENVIRONMENT: str = "development"
    PORT: int = 8000

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

# Validate required settings on startup
if not settings.SECRET_KEY:
    raise ValueError("SECRET_KEY must be set in .env (min 32 chars)")

if not settings.FERNET_KEY:
    raise ValueError("FERNET_KEY must be set in .env (min 32 chars, use: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')")