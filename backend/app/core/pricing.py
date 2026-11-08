"""Rates and cost estimates (ai-evaluation.md section 11).

Each run stores a snapshot of the rates in force, so old costs never change when rates do.
Rates here are defaults: the Settings page manages them in Phase 15.
"""

from decimal import Decimal

from app.core.settings import Settings, is_local
from app.core.taxonomy import Provider
from app.schemas.executions import EstimatedCost, PricingSnapshot, Usage

LOCAL_VERSION = "local-no-charge"
# Published price, checked 2026-11: help.typesafe.ai "How much does Jev cost?". Output is free.
TYPESAFE_JEV_INPUT_PER_MILLION = Decimal("0.042")
TYPESAFE_JEV_VERSION = "typesafe-jev-2026-11"


def local_rates() -> PricingSnapshot:
    return PricingSnapshot(
        input_per_million=Decimal(0), output_per_million=Decimal(0), pricing_version=LOCAL_VERSION
    )


def snapshot_for(provider: Provider, settings: Settings) -> PricingSnapshot | None:
    """The rates for one side, or None when no trustworthy price exists (never guessed)."""
    if settings.mock_providers:
        return None
    if provider is Provider.JEV:
        if is_local(settings.jev_base_url):
            return local_rates()
        return PricingSnapshot(
            input_per_million=TYPESAFE_JEV_INPUT_PER_MILLION,
            output_per_million=Decimal(0),
            pricing_version=TYPESAFE_JEV_VERSION,
        )
    # shortcut: OpenAI rates depend on the chosen model; they arrive with its adapter and Settings.
    return local_rates() if settings.llm_backend == "ollama" else None


def estimate(usage: Usage, rates: PricingSnapshot | None) -> EstimatedCost | None:
    """(input / 1M x input rate) + (output / 1M x output rate). None if anything is missing."""
    if rates is None or usage.input_tokens is None or usage.output_tokens is None:
        return None
    total = usage.input_tokens * rates.input_per_million
    total += usage.output_tokens * rates.output_per_million
    return EstimatedCost(amount=total / 1_000_000, currency=rates.currency)
