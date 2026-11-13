"""Central application configuration.

All environment parsing lives here. Security-critical values are *required*:
if they are missing the application fails loudly at startup rather than
silently downgrading to an insecure mode.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Application --------------------------------------------------------
    app_name: str = Field(default="AI Work Assistant")
    app_env: str = Field(default="development")
    backend_url: str = Field(default="http://localhost:8000")
    frontend_url: str = Field(default="http://localhost:3000")

    # --- Database -----------------------------------------------------------
    database_url: str = Field(default=f"sqlite:///{BACKEND_DIR / 'assistant.db'}")

    # --- Security (required) ------------------------------------------------
    session_secret: str = Field(default="")
    credentials_encryption_key: str = Field(default="")
    cors_origins: str = Field(default="http://localhost:3000")
    session_max_age: int = Field(default=60 * 60 * 24 * 7)  # 7 days

    # --- Google OAuth -------------------------------------------------------
    google_client_id: str = Field(default="")
    google_client_secret: str = Field(default="")
    google_redirect_uri: str = Field(
        default="http://localhost:8000/api/integrations/google/callback"
    )
    google_auth_uri: str = "https://accounts.google.com/o/oauth2/v2/auth"
    google_token_uri: str = "https://oauth2.googleapis.com/token"
    google_userinfo_uri: str = "https://openidconnect.googleapis.com/v1/userinfo"
    gmail_scopes: str = (
        "openid email profile https://www.googleapis.com/auth/gmail.readonly"
    )

    # --- LLM (optional; agent features disabled when unset) ------------------
    llm_provider: str = Field(default="")
    llm_base_url: str = Field(default="")
    llm_model: str = Field(default="")
    llm_api_key: str = Field(default="")

    # --- Activepieces (optional; mail fallback when Google unavailable) ------
    activepieces_base_url: str = Field(default="https://cloud.activepieces.com/api/v1")
    activepieces_api_key: str = Field(default="")
    activepieces_project_id: str = Field(default="")
    activepieces_search_flow_id: str = Field(default="")
    activepieces_get_flow_id: str = Field(default="")

    # --- Validators ---------------------------------------------------------
    @field_validator("cors_origins")
    @classmethod
    def _strip_origins(cls, v: str) -> str:
        return v.strip()

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def google_scope_list(self) -> list[str]:
        return self.gmail_scopes.split()

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"

    @property
    def llm_configured(self) -> bool:
        return bool(self.llm_provider and self.llm_api_key and self.llm_model)

    def validate_security(self) -> None:
        """Raise with actionable messages when security config is missing."""
        problems: list[str] = []
        if not self.session_secret or len(self.session_secret) < 32:
            problems.append(
                "SESSION_SECRET is missing or too short (>=32 chars required). "
                "Generate one: python -c \"import secrets; print(secrets.token_urlsafe(48))\""
            )
        if not self.credentials_encryption_key:
            problems.append(
                "CREDENTIALS_ENCRYPTION_KEY is missing. OAuth tokens must be "
                "encrypted at rest; refusing to start in plaintext mode. "
                "Generate one: python -c \"from cryptography.fernet import "
                "Fernet; print(Fernet.generate_key().decode())\""
            )
        else:
            from cryptography.fernet import Fernet

            try:
                Fernet(self.credentials_encryption_key.encode())
            except Exception:
                problems.append(
                    "CREDENTIALS_ENCRYPTION_KEY is not a valid Fernet key. "
                    "Regenerate: python -c \"from cryptography.fernet import "
                    "Fernet; print(Fernet.generate_key().decode())\""
                )
        if self.is_production and not (
            self.google_client_id and self.google_client_secret
        ):
            problems.append(
                "GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET are required in "
                "production for Gmail integration."
            )
        if problems:
            raise RuntimeError(
                "Configuration errors (fix backend/.env):\n- " + "\n- ".join(problems)
            )


@lru_cache
def get_settings() -> Settings:
    return Settings()
