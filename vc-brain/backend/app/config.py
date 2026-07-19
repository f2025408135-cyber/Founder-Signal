"""Application configuration — pydantic-settings, env-driven."""
from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All settings come from environment variables (or .env file)."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ---- Database ----
    database_url: str = Field(
        default="postgresql+asyncpg://vcbrain:vcbrain@localhost:5432/vcbrain",
        alias="DATABASE_URL",
    )
    database_sync_url: str = Field(
        default="postgresql://vcbrain:vcbrain@localhost:5432/vcbrain",
        alias="DATABASE_SYNC_URL",
    )

    # ---- OpenAI ----
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    worker_model: str = Field(default="gpt-5.6-luna", alias="WORKER_MODEL")
    synthesizer_model: str = Field(default="gpt-5.6-sol", alias="SYNTHESIZER_MODEL")

    # ---- Langfuse ----
    langfuse_public_key: str = Field(default="", alias="LANGFUSE_PUBLIC_KEY")
    langfuse_secret_key: str = Field(default="", alias="LANGFUSE_SECRET_KEY")
    langfuse_host: str = Field(default="http://localhost:3000", alias="LANGFUSE_HOST")
    langfuse_enabled: bool = Field(default=True, alias="LANGFUSE_ENABLED")

    # ---- External APIs ----
    github_token: str = Field(default="", alias="GITHUB_TOKEN")
    producthunt_token: str = Field(default="", alias="PRODUCTHUNT_TOKEN")
    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")
    tavily_api_key: str = Field(default="", alias="TAVILY_API_KEY")

    # ---- App ----
    app_env: str = Field(default="development", alias="APP_ENV")
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")
    app_log_level: str = Field(default="INFO", alias="APP_LOG_LEVEL")

    # ---- Re-score cache ----
    rescore_cache_ttl_minutes: int = Field(default=60, alias="RESCORE_CACHE_TTL_MINUTES")
    stale_cache_hours: int = Field(default=24, alias="STALE_CACHE_HOURS")

    # ---- Embeddings ----
    # Local Sentence-BERT model used for founder-market similarity + dedupe escalation.
    embeddings_model_name: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        alias="EMBEDDINGS_MODEL_NAME",
    )

    @property
    def langfuse_is_configured(self) -> bool:
        return bool(
            self.langfuse_enabled
            and self.langfuse_public_key
            and self.langfuse_secret_key
            and self.langfuse_host
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
