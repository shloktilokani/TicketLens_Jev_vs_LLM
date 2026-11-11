"""Run one provider on one ticket and record the attempt, whatever happens.

The record is written as Running before the provider is called, then completed with the outcome.
A failure is recorded and returned, never raised, so one provider can never stop another.
"""

import logging
import time
from uuid import uuid4

from pydantic import ValidationError
from pymongo.database import Database

from app.core.clock import utc_now
from app.core.pricing import estimate
from app.core.redaction import redact
from app.core.settings import Settings
from app.core.taxonomy import ExecutionStatus, Provider
from app.providers.base import ProviderFailure, ProviderInput, build_input
from app.providers.registry import get_adapter, requested_model
from app.repositories import executions
from app.schemas.classification import NormalizedResult
from app.schemas.executions import Usage
from app.services import app_settings

log = logging.getLogger("ticketlens")


def failed(failure: ProviderFailure) -> dict:
    return {
        "status": failure.status,
        "normalized_result": None,
        "error": {
            "code": failure.kind,
            "http_status": failure.http_status,
            "message": failure.message,
        },
    }


def attempt(provider: Provider, data: ProviderInput, settings: Settings) -> dict:
    try:
        result = get_adapter(provider, settings).classify(data)
    except ProviderFailure as failure:
        return failed(failure) | {
            "request_payload_redacted": redact(failure.request_payload),
            "response_payload_redacted": redact(failure.response_payload),
        }
    except Exception:
        log.exception("Provider %s crashed", provider.value)
        return failed(
            ProviderFailure("unexpected", "Unexpected error. Details are in the backend log.")
        )

    recorded = {
        "actual_model": result.actual_model,
        "request_payload_redacted": redact(result.request_payload),
        "response_payload_redacted": redact(result.response_payload),
        "usage": result.usage.model_dump(),
    }
    try:
        normalized = NormalizedResult(**result.output)
    except ValidationError as exc:
        problems = "; ".join(e["msg"].removeprefix("Value error, ") for e in exc.errors())
        return recorded | failed(
            ProviderFailure(
                "invalid_response", f"The answer did not match the taxonomy: {problems}"
            )
        )
    return recorded | {
        "status": ExecutionStatus.SUCCEEDED,
        "normalized_result": normalized.model_dump(),
        "error": None,
    }


def cost_fields(db: Database, provider: Provider, settings: Settings, usage: dict | None) -> dict:
    """The rates in force now and the estimated cost, stored so history never changes."""
    rates = app_settings.rates_for(db, provider, settings)
    cost = estimate(Usage(**usage), rates) if usage else None
    return {
        "pricing_snapshot": rates.model_dump() if rates else None,
        "estimated_cost": cost.model_dump() if cost else None,
    }


def run(
    db: Database,
    ticket: dict,
    provider: str,
    settings: Settings,
    *,
    comparison_id: str | None = None,
) -> dict:
    provider = Provider(provider)
    settings = app_settings.effective(db, settings)
    prompt_version, instructions = app_settings.active_prompt(db)
    data = build_input(ticket, instructions)
    started, clock = utc_now(), time.perf_counter()
    execution_id = f"exec_{uuid4().hex}"
    executions.insert(
        db,
        {
            "execution_id": execution_id,
            "ticket_id": ticket["ticket_id"],
            "comparison_id": comparison_id,
            "provider": provider,
            "requested_model": requested_model(provider, settings),
            "actual_model": None,
            "status": ExecutionStatus.RUNNING,
            "started_at": started,
            "completed_at": None,
            "duration_ms": None,
            "input_snapshot": data.model_dump(),
            "request_payload_redacted": None,
            "response_payload_redacted": None,
            "normalized_result": None,
            "usage": None,
            "pricing_snapshot": None,
            "estimated_cost": None,
            "error": None,
            "prompt_version": prompt_version,
            "taxonomy_version": data.taxonomy_version,
            "created_at": started,
        },
    )
    outcome = attempt(provider, data, settings)
    outcome |= cost_fields(db, provider, settings, outcome.get("usage"))
    outcome["completed_at"] = utc_now()
    outcome["duration_ms"] = round((time.perf_counter() - clock) * 1000)
    return executions.update(db, execution_id, outcome)
