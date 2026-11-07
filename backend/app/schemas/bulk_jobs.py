from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.core.taxonomy import BulkJobStatus, ExecutionStatus, Provider


class BulkJobCreate(BaseModel):
    """Either an explicit list of tickets or every eligible ticket, never both."""

    ticket_ids: list[str] | None = Field(default=None, min_length=1)
    all_eligible: bool = False
    providers: list[Provider] = Field(min_length=1)

    @model_validator(mode="after")
    def _one_selection(self):
        if (self.ticket_ids is not None) == self.all_eligible:
            raise ValueError("Choose either ticket_ids or all_eligible")
        return self


class BulkOutcome(BaseModel):
    ticket_id: str
    provider: Provider
    status: ExecutionStatus | Literal["Skipped"]
    execution_id: str | None = None


class BulkJob(BaseModel):
    """Persisted progress of one bulk run (data-model.md section 5)."""

    job_id: str
    ticket_ids: list[str] | None = None
    all_eligible: bool = False
    providers: list[Provider]
    status: BulkJobStatus
    total: int = 0
    completed: int = 0
    failed: int = 0
    skipped: int = 0
    outcomes: list[BulkOutcome] = []
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_summary: str | None = None
