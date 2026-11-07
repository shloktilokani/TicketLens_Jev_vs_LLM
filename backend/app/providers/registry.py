"""Which adapter serves each side, from settings.

- Jev side ("jev"): TypeSafe's hosted Jev (needs TYPESAFE_API_KEY) or a local System One server
  such as Ollama running AutoTrust's open JEV models (no key), chosen by JEV_BASE_URL.
- LLM side (key "gpt", kept for now; shown as "LLM"): local Ollama by default, or OpenAI.
- MOCK_PROVIDERS=true replaces both with fake providers.
"""

from urllib.parse import urlparse

from app.core.settings import Settings
from app.core.taxonomy import Provider
from app.providers.base import Adapter, ProviderFailure
from app.providers.jev import JevAdapter
from app.providers.mock import MockProvider
from app.providers.ollama import OllamaAdapter


def is_local(url: str) -> bool:
    return urlparse(url).hostname in ("127.0.0.1", "localhost", "::1")


def provider_labels(settings: Settings) -> dict[str, str]:
    """Human-readable names for the UI. Never contains secrets."""
    if settings.mock_providers:
        return {"jev": "Fake AI", "gpt": "Fake AI"}
    jev = "AutoTrust JEV (local)" if is_local(settings.jev_base_url) else "TypeSafe Jev"
    if settings.llm_backend == "ollama":
        llm = f"Ollama (local) · {settings.ollama_model}"
    else:
        llm = f"OpenAI · {settings.openai_model or 'model not set'}"
    return {"jev": f"{jev} · {settings.jev_model}", "gpt": llm}


def requested_model(provider: Provider, settings: Settings) -> str:
    if settings.mock_providers:
        return f"mock-{provider.value}"
    if provider is Provider.JEV:
        return settings.jev_model
    if settings.llm_backend == "ollama":
        return settings.ollama_model
    return settings.openai_model or "not set"


def jev_adapter(settings: Settings) -> JevAdapter:
    key = settings.typesafe_api_key
    if key is None and not is_local(settings.jev_base_url):
        raise ProviderFailure(
            "not_configured", "Jev is not configured. Add TYPESAFE_API_KEY to backend/.env."
        )
    return JevAdapter(
        base_url=settings.jev_base_url,
        model=settings.jev_model,
        api_key=key.get_secret_value() if key else None,
        threshold=settings.jev_escalation_threshold,
        timeout=settings.provider_timeout_seconds,
        label=provider_labels(settings)["jev"].split(" · ")[0],
    )


def llm_adapter(settings: Settings) -> OllamaAdapter:
    if settings.llm_backend == "ollama":
        return OllamaAdapter(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
            timeout=settings.provider_timeout_seconds,
        )
    if settings.openai_api_key is None:
        raise ProviderFailure(
            "not_configured", "OpenAI is not configured. Add OPENAI_API_KEY to backend/.env."
        )
    # shortcut: the OpenAI adapter is not built yet; it arrives with Phase 10 when a key exists.
    raise ProviderFailure("not_configured", "The OpenAI connection is not built yet (Phase 10).")


def get_adapter(provider: Provider | str, settings: Settings) -> Adapter:
    """The adapter to call, or a not_configured failure explaining what is missing."""
    provider = Provider(provider)
    if settings.mock_providers:
        return MockProvider(provider, settings.mock_delay_seconds)
    return jev_adapter(settings) if provider is Provider.JEV else llm_adapter(settings)
