from fastapi import APIRouter, Request

from app.providers.registry import is_local, provider_labels

router = APIRouter(prefix="/api/providers", tags=["providers"])


@router.get("/status")
def provider_status(request: Request) -> dict:
    """Whether each side can run, and what it is called. Key values never leave the backend."""
    settings = request.app.state.settings
    labels = provider_labels(settings)
    mock = settings.mock_providers
    jev_ready = mock or is_local(settings.jev_base_url) or settings.typesafe_api_key is not None
    llm_ready = mock or settings.llm_backend == "ollama" or settings.openai_api_key is not None
    return {
        "jev": {"configured": jev_ready, "label": labels["jev"]},
        "gpt": {"configured": llm_ready, "label": labels["gpt"]},
    }
