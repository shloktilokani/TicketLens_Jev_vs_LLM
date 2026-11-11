"""Backend settings: the only module that reads environment variables or backend/.env."""

from functools import lru_cache
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    # Unknown keys in backend/.env are an error, so a misspelt variable is caught at startup.
    # Empty values count as unset, so a copied .env.example reads as "not configured".
    # Errors never echo inputs, so a bad setting cannot print a database password.
    model_config = SettingsConfigDict(
        env_file=ENV_FILE, extra="forbid", env_ignore_empty=True, hide_input_in_errors=True
    )

    app_env: str = "development"
    app_name: str = "TicketLens"
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    frontend_origin: str = "http://localhost:5173"

    mongodb_uri: str = Field(default="mongodb://127.0.0.1:27017", repr=False)
    mongodb_database: str = "ticketlens"

    # Optional on purpose: the app must start without keys (AGENTS.md). Provider calls fail
    # with a clear "not configured" error instead.
    typesafe_api_key: SecretStr | None = None
    openai_api_key: SecretStr | None = None

    # Jev side: TypeSafe's hosted API, or a local System One server (Ollama with AutoTrust JEV).
    jev_base_url: str = "https://api.typesafe.ai"
    jev_model: str = "jev-latest"
    # LLM side: a local Ollama model. "openai" is accepted, but its adapter is deferred (owner
    # decision), so runs record not_configured.
    llm_backend: Literal["ollama", "openai"] = "ollama"
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen3:8b"
    openai_model: str | None = None

    provider_timeout_seconds: float = Field(default=45, gt=0)
    bulk_concurrency: int = Field(default=2, ge=1)
    jev_escalation_threshold: float = Field(default=0.5, ge=0, le=1)

    # Fake Jev and LLM: no network, no cost. Results are labelled mock-*, never passing as real.
    mock_providers: bool = False
    # Fake thinking time so the UI timers visibly run: Jev waits this long, the LLM twice as long.
    mock_delay_seconds: float = Field(default=1.5, ge=0, le=30)

    log_level: str = "INFO"

    # The app has no login. Set true only when a proxy or VPN in front of it restricts access.
    access_control_confirmed: bool = False

    @model_validator(mode="after")
    def _production_is_safe(self):
        """Refuse to start an unsafe production setup, instead of exposing it quietly."""
        if self.app_env != "production":
            return self
        problems = []
        if is_local(self.mongodb_uri):
            problems.append("MONGODB_URI must point to a production database, not this computer.")
        origin = self.frontend_origin
        if not origin.startswith("https://") or "*" in origin:
            problems.append("FRONTEND_ORIGIN must be one exact https:// address.")
        if self.mock_providers:
            problems.append("MOCK_PROVIDERS must be false.")
        if not self.access_control_confirmed:
            problems.append(
                "ACCESS_CONTROL_CONFIRMED must be true: TicketLens has no login, so production "
                "needs a proxy or VPN that restricts who can reach it."
            )
        if problems:
            raise ValueError(" ".join(problems))
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


def is_local(url: str) -> bool:
    return urlparse(url).hostname in ("127.0.0.1", "localhost", "::1")
