"""Centralized configuration loaded from environment."""
from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
 
 
class Settings(BaseSettings):
    """All env-driven settings live here."""
 
    model_config = SettingsConfigDict(
        env_file=(".env.local", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )
 
    anthropic_api_key: str = Field(..., description="Anthropic API key")
    openai_api_key: str | None = Field(default=None, description="OpenAI API key (optional)")
    default_anthropic_model: str = Field(default="claude-haiku-4-5")
    default_openai_model: str = Field(default="gpt-4o-mini")
 
 
@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]