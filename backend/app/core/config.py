from typing import List, Union, Optional
from pathlib import Path
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import json
import os

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    PROJECT_NAME: str = "FocusBoard API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"  # "development" | "staging" | "production" | "testing"
    DEBUG: bool = False

    # Security
    SECRET_KEY: str = "focusboard_production_super_secret_jwt_key_change_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database
    DATABASE_URL: str = "sqlite:///./focusboard.db"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_PRE_PING: bool = True

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 120

    # File Storage & Uploads
    UPLOAD_MAX_BYTES: int = 20 * 1024 * 1024  # 20 MB
    ALLOWED_UPLOAD_EXTENSIONS: List[str] = [".png", ".jpg", ".jpeg", ".pdf", ".txt", ".csv", ".json", ".zip"]

    # Redis (Optional cache/queue)
    REDIS_URL: Optional[str] = None

    # CORS
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]

    # AI Configuration (Phase 14)
    AI_PROVIDER: str = "mock"  # "mock" | "gemini" | "openai"
    AI_API_KEY: Optional[str] = None
    AI_MODEL: str = "gemini-1.5-flash"
    AI_TIMEOUT_SECONDS: int = 30
    AI_MAX_OUTPUT_TOKENS: int = 2048

    # Email & Notifications Configuration (Phase 15)
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 1025
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAIL_FROM: str = "notifications@focusboard.io"
    EMAIL_ENABLED: bool = False

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def resolve_database_url(cls, v: Optional[str]) -> str:
        if not v or v == "sqlite:///./focusboard.db":
            # If default SQLite is used, resolve to the shared focusboard.db in project root
            try:
                root_db = Path(__file__).resolve().parents[3] / "focusboard.db"
                if root_db.exists():
                    return f"sqlite:///{root_db.as_posix()}"
            except Exception:
                pass
        return v or "sqlite:///./focusboard.db"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, str) and v.startswith("["):
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except Exception:
                pass
        return v if isinstance(v, list) else []

settings = Settings()
