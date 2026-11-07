"""Ticket workflows that turn API input into stored documents."""

from uuid import uuid4

from pymongo.database import Database

from app.core.clock import utc_now
from app.core.taxonomy import TAXONOMY_VERSION, TicketStatus
from app.repositories import tickets
from app.schemas.classification import Classification, FinalClassification
from app.schemas.tickets import TicketCreate, TicketUpdate

# Flat API field -> nested document path (data-model.md section 1).
FIELD_PATHS = {
    "customer_name": "customer.name",
    "customer_email": "customer.email",
    "order_id": "order.order_id",
    "product_name": "order.product_name",
}


def create(
    db: Database, data: TicketCreate, *, source: dict | None = None, is_sample: bool = False
) -> dict:
    now = utc_now()
    doc = {
        "ticket_id": tickets.next_ticket_id(db),
        "title": data.title,
        "description": data.description,
        "customer": {"name": data.customer_name, "email": data.customer_email},
        "order": {"order_id": data.order_id, "product_name": data.product_name},
        "submission_channel": data.submission_channel,
        "status": TicketStatus.OPEN,
        "final_classification": None,
        "operator_notes": [],
        "source": source or {"type": "manual", "import_batch_id": None, "source_fingerprint": None},
        "is_sample": is_sample,
        "taxonomy_version": TAXONOMY_VERSION,
        "created_at": now,
        "updated_at": now,
    }
    tickets.insert(db, doc)
    return doc


def update(db: Database, ticket_id: str, data: TicketUpdate) -> dict | None:
    changes = {FIELD_PATHS.get(k, k): v for k, v in data.model_dump(exclude_unset=True).items()}
    return tickets.update(db, ticket_id, {"$set": changes | {"updated_at": utc_now()}})


def add_note(db: Database, ticket_id: str, text: str) -> dict | None:
    now = utc_now()
    note = {"note_id": f"note_{uuid4().hex}", "text": text, "created_at": now}
    return tickets.update(
        db, ticket_id, {"$push": {"operator_notes": note}, "$set": {"updated_at": now}}
    )


def set_classification(db: Database, ticket_id: str, data: Classification) -> dict | None:
    """Store an operator's manual classification. Never called automatically."""
    now = utc_now()
    final = FinalClassification(**data.model_dump(), manually_edited=True, updated_at=now)
    return tickets.update(
        db, ticket_id, {"$set": {"final_classification": final.model_dump(), "updated_at": now}}
    )
