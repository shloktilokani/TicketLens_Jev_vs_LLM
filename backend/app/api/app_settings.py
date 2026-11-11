from collections.abc import Callable
from typing import Literal

from fastapi import APIRouter, HTTPException, Request

from app.api.deps import Db
from app.providers.base import ProviderFailure
from app.schemas.app_settings import PricingUpdate, PromptUpdate, SettingsUpdate, TaxonomyUpdate
from app.services import app_settings as service

router = APIRouter(prefix="/api/settings", tags=["settings"])


def saved(request: Request, db: Db, write: Callable[[], None]) -> dict:
    """Apply a write and return the new settings, turning a refusal into a clear HTTP error."""
    try:
        write()
    except service.SettingsError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from None
    return service.view(db, request.app.state.settings)


@router.get("")
def get_settings(request: Request, db: Db) -> dict:
    """Saved settings and provider status. API keys are never included."""
    return service.view(db, request.app.state.settings)


@router.patch("")
def update_settings(data: SettingsUpdate, request: Request, db: Db) -> dict:
    settings = request.app.state.settings
    return saved(request, db, lambda: service.update_values(db, settings, data))


@router.put("/prompt")
def update_prompt(data: PromptUpdate, request: Request, db: Db) -> dict:
    """Save a new prompt version. Earlier runs keep the version they used."""
    return saved(request, db, lambda: service.save_prompt(db, data.instructions))


@router.put("/taxonomy")
def update_taxonomy(data: TaxonomyUpdate, request: Request, db: Db) -> dict:
    """Save a new taxonomy version. Labels used by stored records cannot be removed or renamed."""
    return saved(request, db, lambda: service.save_taxonomy(db, data))


@router.put("/pricing")
def update_pricing(data: PricingUpdate, request: Request, db: Db) -> dict:
    """Replace the rate table. Earlier runs keep the rates saved with them."""
    return saved(request, db, lambda: service.save_pricing(db, data))


@router.get("/models/{side}")
def list_models(side: Literal["jev", "llm"], request: Request) -> dict:
    """The models this side's server offers, or a safe explanation of why it could not say."""
    try:
        return {"models": service.available_models(request.app.state.settings, side), "error": None}
    except ProviderFailure as failure:
        return {"models": [], "error": failure.message}
