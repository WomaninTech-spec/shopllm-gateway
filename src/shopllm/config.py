"""Centralized configuration loaded from environment."""
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(PROJECT_ROOT / ".env.local", PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    anthropic_api_key: str = Field(..., description="Anthropic API key")
    openai_api_key: str | None = Field(default=None, description="OpenAI API key (optional)")
    default_anthropic_model: str = Field(default="claude-haiku-4-5")
    default_openai_model: str = Field(default="gpt-4o-mini")
    database_url: str = Field(default="postgresql+asyncpg://shopllm:shopllm@localhost:5432/shopllm")
    api_key_prefix: str = Field(default="sk-slm-")


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
