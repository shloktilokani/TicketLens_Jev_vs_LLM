"""Operator settings saved in MongoDB, layered over the environment defaults.

Every run stores the prompt, taxonomy and rate versions it used, so editing these never changes
history. API keys stay in backend/.env: nothing here can read or write them.
"""

import httpx
from pymongo.database import Database

from app.core import taxonomy
from app.core.clock import utc_now
from app.core.pricing import snapshot_for
from app.core.settings import Settings, is_local
from app.core.taxonomy import Provider
from app.providers import definitions
from app.providers.base import PROMPT_VERSION, ProviderFailure
from app.providers.http import get_json
from app.providers.registry import provider_labels, provider_ready, requested_model
from app.repositories import app_settings as store
from app.schemas.app_settings import PricingUpdate, SettingsUpdate, TaxonomyUpdate
from app.schemas.executions import PricingSnapshot

JEV_ALIAS = "jev-latest"  # TypeSafe's documented alias, which its model list may not name
MODEL_LIST_TIMEOUT_SECONDS = 10


class SettingsError(ValueError):
    def __init__(self, status_code: int, message: str):
        super().__init__(message)
        self.status_code = status_code


def next_version(version: str) -> str:
    major, minor = version.split(".")
    return f"{major}.{int(minor) + 1}"


def load_taxonomy(db: Database) -> None:
    """Make the saved taxonomy active. Called on startup and after each change."""
    saved = store.get(db).get("taxonomy")
    if saved:
        taxonomy.set_active(saved["version"], saved["categories"])
    else:
        taxonomy.reset()


def effective(db: Database, settings: Settings) -> Settings:
    """The environment settings with the operator's saved choices applied."""
    saved = store.get(db)
    changes = {
        key: saved[key]
        for key in ("jev_model", "jev_escalation_threshold", "bulk_concurrency")
        if key in saved
    }
    if "llm_model" in saved:
        field = "ollama_model" if settings.llm_backend == "ollama" else "openai_model"
        changes[field] = saved["llm_model"]
    return settings.model_copy(update=changes)


def active_prompt(db: Database) -> tuple[str, str]:
    """(version, instructions) for new runs."""
    prompt = store.get(db).get("prompt")
    if prompt:
        return prompt["version"], prompt["instructions"]
    return PROMPT_VERSION, definitions.INSTRUCTIONS


def rates_for(db: Database, provider: Provider, settings: Settings) -> PricingSnapshot | None:
    """Saved rates for this side's current model, else the built-in ones. Fake runs have none."""
    if settings.mock_providers:
        return None
    model = requested_model(provider, settings)
    for entry in store.get(db).get("pricing", []):
        if entry["provider"] == provider and entry["model"] == model:
            return PricingSnapshot(
                input_per_million=entry["input_per_million"],
                output_per_million=entry["output_per_million"],
                pricing_version=entry["pricing_version"],
            )
    return snapshot_for(provider, settings)


def available_models(
    settings: Settings, side: str, client: httpx.Client | None = None
) -> list[str]:
    """The models this side's server offers. Raises a safe ProviderFailure if it cannot say."""
    if settings.mock_providers:
        return [requested_model(Provider.JEV if side == "jev" else Provider.GPT, settings)]
    headers = {}
    if side == "jev":
        base, label = settings.jev_base_url, "Jev"
        if settings.typesafe_api_key and not is_local(base):
            headers["Authorization"] = f"Bearer {settings.typesafe_api_key.get_secret_value()}"
    elif settings.llm_backend == "ollama":
        base, label = settings.ollama_base_url, "Ollama"
    else:
        raise ProviderFailure("not_configured", "The OpenAI connection is not built yet.")
    body = get_json(
        base.rstrip("/") + "/v1/models",
        label=label,
        timeout=MODEL_LIST_TIMEOUT_SECONDS,
        headers=headers,
        client=client,
    )
    try:
        return sorted(item["id"] for item in body["data"])
    except (KeyError, TypeError):
        raise ProviderFailure("invalid_response", f"{label} sent an unreadable list.") from None


def check_model(settings: Settings, side: str, model: str) -> None:
    """Refuse a model the server says it lacks. If the server is down, trust the operator."""
    if settings.mock_providers or (side == "jev" and model == JEV_ALIAS):
        return
    try:
        models = available_models(settings, side)
    except ProviderFailure:
        return
    if model not in models:
        raise SettingsError(422, f"{model} is not available. Available: {', '.join(models)}")


def view(db: Database, settings: Settings) -> dict:
    active = effective(db, settings)
    saved = store.get(db)
    version, instructions = active_prompt(db)
    canon = taxonomy.as_dict()
    labels = provider_labels(active)
    return {
        "providers": {
            key: {"configured": provider_ready(key, active), "label": labels[key]}
            for key in ("jev", "gpt")
        },
        "jev_model": requested_model(Provider.JEV, active),
        "llm_model": requested_model(Provider.GPT, active),
        "jev_escalation_threshold": active.jev_escalation_threshold,
        "bulk_concurrency": active.bulk_concurrency,
        "prompt": {
            "version": version,
            "instructions": instructions,
            "history": saved.get("prompt_history", [])[::-1],
        },
        "taxonomy": {"version": canon["version"], "categories": canon["categories"]},
        "pricing": saved.get("pricing", []),
        "updated_at": saved.get("updated_at"),
    }


def update_values(db: Database, settings: Settings, data: SettingsUpdate) -> None:
    changes = data.model_dump(exclude_unset=True)
    if "jev_model" in changes:
        check_model(settings, "jev", changes["jev_model"])
    if "llm_model" in changes:
        check_model(settings, "llm", changes["llm_model"])
    store.update(db, {"$set": changes | {"updated_at": utc_now()}})


def save_prompt(db: Database, instructions: str) -> None:
    version, current = active_prompt(db)
    now = utc_now()
    if not store.get(db).get("prompt_history"):  # keep the starting prompt in the history too
        store.update(
            db,
            {
                "$push": {
                    "prompt_history": {
                        "version": version,
                        "instructions": current,
                        "created_at": now,
                    }
                }
            },
        )
    new = {"version": next_version(version), "instructions": instructions, "created_at": now}
    store.update(
        db,
        {"$set": {"prompt": new, "updated_at": now}, "$push": {"prompt_history": new}},
    )


def save_taxonomy(db: Database, data: TaxonomyUpdate) -> None:
    current = taxonomy.as_dict()
    removed = {
        (category, sub)
        for category, subs in current["categories"].items()
        for sub in subs
        if sub not in data.categories.get(category, [])
    }
    blocked = sorted(sub for _, sub in removed & store.labels_in_use(db))
    if blocked:
        raise SettingsError(
            409,
            "These labels are used by stored records, so they cannot be removed or renamed: "
            + ", ".join(blocked),
        )
    now = utc_now()
    new = {
        "version": next_version(current["version"]),
        "categories": data.categories,
        "created_at": now,
    }
    store.update(
        db,
        {"$set": {"taxonomy": new, "updated_at": now}, "$push": {"taxonomy_history": new}},
    )
    load_taxonomy(db)


def save_pricing(db: Database, data: PricingUpdate) -> None:
    now = utc_now()
    version = f"settings-{now.strftime('%Y-%m-%dT%H:%M:%SZ')}"
    entries = [entry.model_dump() | {"pricing_version": version} for entry in data.entries]
    store.update(db, {"$set": {"pricing": entries, "updated_at": now}})
