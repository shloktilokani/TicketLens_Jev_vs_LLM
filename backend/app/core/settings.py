"""Backend settings: the only module that reads environment variables or backend/.env."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    # Unknown keys in backend/.env are an error, so a misspelt variable is caught at startup.
    # Empty values count as unset, so a copied .env.example reads as "not configured".
    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="forbid", env_ignore_empty=True)

    app_env: str = "development"
    app_name: str = "TicketLens"
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    frontend_origin: str = "http://localhost:5173"

    mongodb_uri: str = "mongodb://127.0.0.1:27017"
    mongodb_database: str = "ticketlens"

    # Optional on purpose: the app must start without keys (AGENTS.md). Provider calls fail
    # with a clear "not configured" error instead.
    typesafe_api_key: SecretStr | None = None
    openai_api_key: SecretStr | None = None

    jev_model: str = "jev-latest"
    openai_model: str | None = None

    provider_timeout_seconds: float = Field(default=45, gt=0)
    bulk_concurrency: int = Field(default=2, ge=1)
    jev_escalation_threshold: float = Field(default=0.5, ge=0, le=1)

    # Fake Jev and GPT: no network, no cost. Results are labelled mock-*, never passing as real.
    mock_providers: bool = False
    # Fake thinking time so the UI timers visibly run: Jev waits this long, GPT twice as long.
    mock_delay_seconds: float = Field(default=1.5, ge=0, le=30)

    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()
