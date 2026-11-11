from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

from app.core.taxonomy import TAXONOMY_VERSION, ExecutionStatus, Provider
from app.schemas.classification import NormalizedResult


class Usage(BaseModel):
    """Token counts. None means the provider did not report them; never guessed."""

    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)
    total_tokens: int | None = Field(default=None, ge=0)
    usage_source: Literal["provider_reported", "estimated", "unavailable"] = "unavailable"


class PricingSnapshot(BaseModel):
    """The rates in force when the call ran, so old costs never change when rates do."""

    currency: str = "USD"
    input_per_million: Decimal = Field(ge=0)
    output_per_million: Decimal = Field(ge=0)
    pricing_version: str


class EstimatedCost(BaseModel):
    # Decimal, not float or integer micro-units: Jev costs can be a few millionths of a dollar.
    amount: Decimal | None = None
    currency: str = "USD"
    is_estimate: bool = True


class ProviderError(BaseModel):
    """A user-safe error. Technical details stay in backend logs."""

    code: str | None = None
    http_status: int | None = None
    message: str


class Execution(BaseModel):
    """One provider attempt, including failures (data-model.md section 2)."""

    execution_id: str
    ticket_id: str
    comparison_id: str | None = None
    provider: Provider
    requested_model: str
    actual_model: str | None = None
    status: ExecutionStatus
    started_at: datetime
    completed_at: datetime | None = None
    duration_ms: int | None = Field(default=None, ge=0)
    input_snapshot: dict
    request_payload_redacted: dict | None = None
    response_payload_redacted: dict | None = None
    normalized_result: NormalizedResult | None = None
    usage: Usage | None = None
    pricing_snapshot: PricingSnapshot | None = None
    estimated_cost: EstimatedCost | None = None
    error: ProviderError | None = None
    prompt_version: str
    taxonomy_version: str = TAXONOMY_VERSION
