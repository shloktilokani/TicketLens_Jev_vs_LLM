"""Ticket workflows that turn API input into stored documents."""

from uuid import uuid4

from pymongo.database import Database

from app.core.clock import utc_now
from app.core.taxonomy import ExecutionStatus, TicketStatus, active_version
from app.repositories import executions, tickets
from app.schemas.classification import FinalClassification, FinalClassificationInput
from app.schemas.tickets import TicketCreate, TicketUpdate

# Flat API field -> nested document path (data-model.md section 1).
FIELD_PATHS = {
    "customer_name": "customer.name",
    "customer_email": "customer.email",
    "order_id": "order.order_id",
    "product_name": "order.product_name",
}


class RunNotUsable(ValueError):
    """The named AI run cannot supply this ticket's final classification."""


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
        "taxonomy_version": active_version(),
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


def run_result(db: Database, ticket_id: str, execution_id: str) -> dict:
    """The validated answer of one of this ticket's successful runs."""
    run = executions.get(db, execution_id)
    if run is None or run["ticket_id"] != ticket_id:
        raise RunNotUsable("That AI run does not belong to this ticket.")
    if run["status"] != ExecutionStatus.SUCCEEDED or not run.get("normalized_result"):
        raise RunNotUsable("Only a successful AI run can supply the final classification.")
    return run["normalized_result"]


def set_classification(db: Database, ticket_id: str, data: FinalClassificationInput) -> dict | None:
    """Store the operator's final answer. Never called automatically."""
    now = utc_now()
    fields = data.model_dump(exclude={"selected_from_execution_id"})
    run_id = data.selected_from_execution_id
    result = run_result(db, ticket_id, run_id) if run_id else None
    edited = result is None or any(fields[name] != result[name] for name in fields)
    final = FinalClassification(
        **fields,
        selected_from_execution_id=run_id,
        manually_edited=edited,
        taxonomy_version=active_version(),
        updated_at=now,
    )
    return tickets.update(
        db, ticket_id, {"$set": {"final_classification": final.model_dump(), "updated_at": now}}
    )
