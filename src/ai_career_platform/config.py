from __future__ import annotations
import os
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

_env_path = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(_env_path) if _env_path.exists() else ".env", extra="ignore")

    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    OPENROUTER_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "")
    OLLAMA_API_KEY: str = ""
    SERPER_API_KEY: str = ""
    DATABASE_URL: str = "sqlite:///./career_platform.db"
    SECRET_KEY: str = ""
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    MAX_UPLOAD_SIZE_BYTES: int = 10 * 1024 * 1024
    ALLOWED_UPLOAD_EXTENSIONS: str = ".pdf,.docx,.txt"
    ACCESS_TOKEN_EXPIRE_HOURS: int = 24

    def validated_secret_key(self) -> str:
        key = self.SECRET_KEY
        if not key or key in ("replace-me-with-a-secure-secret", "dev-secret-change-me"):
            raise ValueError(
                "SECRET_KEY must be set. "
                "Generate: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
            )
        return key

    @property
    def allowed_upload_extensions_set(self) -> set:
        return {e.strip().lower() for e in self.ALLOWED_UPLOAD_EXTENSIONS.split(",") if e.strip()}


settings = Settings()
