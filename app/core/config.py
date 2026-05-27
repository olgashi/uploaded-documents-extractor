from typing import Any, Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    # --- Database ---
    DATABASE_URL: str

    # --- Auth ---
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # --- OpenAI ---
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o"

    # --- Rate limiting (slowapi format: "N/period") ---
    RATE_LIMIT_EXTRACT: str = "5/minute"
    RATE_LIMIT_API: str = "100/minute"

    # --- Application ---
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    LOG_LEVEL: str = "INFO"
    ALLOWED_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # --- Seeded admin (created on first startup if user table is empty) ---
    ADMIN_EMAIL: str
    ADMIN_PASSWORD: str

    # --- Validators ---

    @field_validator("SECRET_KEY")
    @classmethod
    def secret_key_min_length(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters")
        return v

    @field_validator("ADMIN_PASSWORD")
    @classmethod
    def admin_password_min_length(cls, v: str) -> str:
        if len(v) < 12:
            raise ValueError("ADMIN_PASSWORD must be at least 12 characters")
        return v

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        if not any(v.startswith(p) for p in ("postgresql", "postgres", "sqlite")):
            raise ValueError("DATABASE_URL must be a PostgreSQL (or SQLite for tests) URL")
        return v

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("["):
                import json
                return json.loads(v)
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @property
    def async_database_url(self) -> str:
        """Normalise any postgres:// variant to postgresql+asyncpg:// for SQLAlchemy async."""
        url = self.DATABASE_URL
        replacements = {
            "postgres://": "postgresql+asyncpg://",
            "postgresql://": "postgresql+asyncpg://",
        }
        for old, new in replacements.items():
            if url.startswith(old):
                return url.replace(old, new, 1)
        return url

    @property
    def sync_database_url(self) -> str:
        """psycopg2-compatible URL used by Alembic (sync)."""
        url = self.DATABASE_URL
        replacements = {
            "postgresql+asyncpg://": "postgresql://",
            "postgres://": "postgresql://",
        }
        for old, new in replacements.items():
            if url.startswith(old):
                return url.replace(old, new, 1)
        return url


settings = Settings()
