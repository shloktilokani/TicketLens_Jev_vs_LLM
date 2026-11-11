from datetime import datetime
from typing import Annotated, Literal

from pydantic import (
    AfterValidator,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    StringConstraints,
    model_validator,
)

from app.core.taxonomy import TAXONOMY_VERSION, Channel, TicketStatus
from app.schemas.classification import FinalClassification


def _not_blank(value: str) -> str:
    if not value.strip():
        raise ValueError("must not be blank")
    return value


def _blank_to_none(value):
    return (value.strip() or None) if isinstance(value, str) else value


ShortText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
OptionalText = Annotated[
    Annotated[str, StringConstraints(max_length=200)] | None, BeforeValidator(_blank_to_none)
]
# Kept exactly as typed (no trimming), so the provider sees the original text.
LongText = Annotated[str, StringConstraints(max_length=10_000), AfterValidator(_not_blank)]
# shortcut: a format check only, not deliverability; enough for synthetic demo data.
Email = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True, to_lower=True, max_length=254, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    ),
]


class TicketCreate(BaseModel):
    """Manual ticket input, matching the create form and the CSV columns."""

    title: ShortText
    description: LongText
    customer_name: ShortText
    customer_email: Email
    order_id: OptionalText = None
    product_name: OptionalText = None
    submission_channel: Channel


class TicketUpdate(BaseModel):
    """Partial update. Omitted fields stay unchanged; null is accepted only for optional fields."""

    model_config = ConfigDict(extra="forbid")

    # Defaults are not validated, so an omitted field is fine while an explicit null is rejected.
    title: ShortText = None
    description: LongText = None
    customer_name: ShortText = None
    customer_email: Email = None
    order_id: OptionalText = None
    product_name: OptionalText = None
    submission_channel: Channel = None
    status: TicketStatus = None

    @model_validator(mode="after")
    def _not_empty(self):
        if not self.model_fields_set:
            raise ValueError("Nothing to update")
        return self


class NoteCreate(BaseModel):
    text: LongText


class Customer(BaseModel):
    name: str
    email: str


class OrderInfo(BaseModel):
    order_id: str | None = None
    product_name: str | None = None


class Note(BaseModel):
    note_id: str
    text: str
    created_at: datetime


class Source(BaseModel):
    type: Literal["manual", "csv_import"] = "manual"
    import_batch_id: str | None = None
    source_fingerprint: str | None = None


class LatestRun(BaseModel):
    provider: str
    status: str
    started_at: datetime


class Ticket(BaseModel):
    """A stored ticket, as returned by the API (data-model.md section 1)."""

    ticket_id: str
    title: str
    description: str
    customer: Customer
    order: OrderInfo
    submission_channel: Channel
    status: TicketStatus
    final_classification: FinalClassification | None = None
    latest_run: LatestRun | None = None
    operator_notes: list[Note] = []
    source: Source = Source()
    is_sample: bool = False
    taxonomy_version: str = TAXONOMY_VERSION
    created_at: datetime
    updated_at: datetime


class TicketPage(BaseModel):
    items: list[Ticket]
    total: int
    page: int
    page_size: int
