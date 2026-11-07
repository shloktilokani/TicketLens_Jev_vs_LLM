from app.core.settings import Settings
from app.core.taxonomy import Provider
from app.providers.base import Adapter, ProviderFailure
from app.providers.mock import MockProvider

LABELS = {Provider.JEV: "Jev", Provider.GPT: "GPT"}
KEYS = {
    Provider.JEV: ("typesafe_api_key", "TYPESAFE_API_KEY"),
    Provider.GPT: ("openai_api_key", "OPENAI_API_KEY"),
}


def requested_model(provider: Provider, settings: Settings) -> str:
    if settings.mock_providers:
        return f"mock-{provider.value}"
    if provider is Provider.JEV:
        return settings.jev_model
    return settings.openai_model or "not set"


def get_adapter(provider: Provider, settings: Settings) -> Adapter:
    """The adapter to call, or a not_configured failure explaining what is missing."""
    if settings.mock_providers:
        return MockProvider(provider, settings.mock_delay_seconds)
    attribute, env_name = KEYS[provider]
    if getattr(settings, attribute) is None:
        raise ProviderFailure(
            "not_configured",
            f"{LABELS[provider]} is not configured. Add {env_name} to backend/.env.",
        )
    # shortcut: no live adapters yet; Jev arrives in Phase 9 and GPT in Phase 10.
    phase = 9 if provider is Provider.JEV else 10
    raise ProviderFailure(
        "not_configured", f"The live {LABELS[provider]} integration arrives in Phase {phase}."
    )
