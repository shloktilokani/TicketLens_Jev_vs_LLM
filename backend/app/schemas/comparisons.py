from datetime import datetime

from pydantic import BaseModel

from app.core.taxonomy import ComparisonStatus


class FieldComparison(BaseModel):
    jev: str | bool | None = None
    gpt: str | bool | None = None
    match: bool | None = None  # None when either side has no value to compare


class Comparison(BaseModel):
    """Jev vs GPT on the five shared fields. Never picks a winner (data-model.md section 4)."""

    comparison_id: str
    ticket_id: str
    jev_execution_id: str | None = None
    gpt_execution_id: str | None = None
    status: ComparisonStatus
    field_comparison: dict[str, FieldComparison] = {}
    agreement_count: int = 0
    comparable_field_count: int = 0
    agreement_rate: float | None = None
    created_at: datetime


class ComparisonCreate(BaseModel):
    ticket_id: str
    jev_execution_id: str
    gpt_execution_id: str
