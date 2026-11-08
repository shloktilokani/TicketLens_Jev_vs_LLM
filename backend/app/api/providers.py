from fastapi import APIRouter, Request

from app.api.deps import Db
from app.services import app_settings

router = APIRouter(prefix="/api/providers", tags=["providers"])


@router.get("/status")
def provider_status(request: Request, db: Db) -> dict:
    """Whether each side can run, and what it is called. Key values never leave the backend."""
    return app_settings.view(db, request.app.state.settings)["providers"]
