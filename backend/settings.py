"""Application settings loaded from environment variables."""

from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """Central application configuration."""

    app_name: str = "Agentic PRD Generation API"
    app_version: str = "0.1.0"
    environment: Literal["development", "test", "production"] = "development"
    debug: bool = False

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:8501",
            "http://127.0.0.1:8501",
        ]
    )

    state_backend: Literal["auto", "redis", "memory"] = "auto"
    redis_url: str = "redis://localhost:6379/0"
    redis_ttl_seconds: int = 60 * 60 * 24 * 7

    openai_api_key: str | None = None
    google_api_key: str | None = None
    openai_model: str = "gpt-4.1-mini"
    google_model: str = "gemini-2.5-flash"
    default_temperature: float = 0.2
    max_output_tokens: int = 4096
    request_timeout_seconds: float = 60.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
