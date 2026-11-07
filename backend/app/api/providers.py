from fastapi import APIRouter, Request

router = APIRouter(prefix="/api/providers", tags=["providers"])


@router.get("/status")
def provider_status(request: Request) -> dict:
    """Whether each provider has a key. Only booleans: key values never leave the backend."""
    settings = request.app.state.settings
    return {
        "jev": {"configured": settings.typesafe_api_key is not None},
        "gpt": {"configured": settings.openai_api_key is not None},
    }
