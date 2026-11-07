import logging
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Query
from pymongo.errors import PyMongoError

from app.api.deps import Db
from app.core.taxonomy import Category, Priority, TicketStatus
from app.repositories import tickets
from app.schemas.classification import Classification
from app.schemas.tickets import NoteCreate, Ticket, TicketCreate, TicketPage, TicketUpdate
from app.services import tickets as service

router = APIRouter(prefix="/api/tickets", tags=["tickets"])
log = logging.getLogger("ticketlens")


def found(ticket: dict | None) -> dict:
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


@router.post("", status_code=201, response_model=Ticket)
def create_ticket(data: TicketCreate, db: Db):
    """Create a ticket with status Open. AI never runs automatically on save."""
    return service.create(db, data)


@router.get("", response_model=TicketPage)
def list_tickets(
    db: Db,
    q: Annotated[
        str | None, Query(max_length=200, description="Ticket ID, title, name, email or order ID")
    ] = None,
    category: Category | None = None,
    priority: Priority | None = None,
    status: TicketStatus | None = None,
    sort: Literal["created_at", "priority"] = "created_at",
    order: Literal["asc", "desc"] = "desc",
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
):
    items, total = tickets.search(
        db,
        q=q,
        filters={
            "final_classification.category": category,
            "final_classification.priority": priority,
            "status": status,
        },
        sort=sort,
        descending=order == "desc",
        page=page,
        page_size=page_size,
    )
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/{ticket_id}", response_model=Ticket)
def get_ticket(ticket_id: str, db: Db):
    return found(tickets.get(db, ticket_id))


@router.patch("/{ticket_id}", response_model=Ticket)
def update_ticket(ticket_id: str, data: TicketUpdate, db: Db):
    return found(service.update(db, ticket_id, data))


@router.post("/{ticket_id}/notes", status_code=201, response_model=Ticket)
def add_note(ticket_id: str, data: NoteCreate, db: Db):
    return found(service.add_note(db, ticket_id, data.text))


@router.put("/{ticket_id}/final-classification", response_model=Ticket)
def set_final_classification(ticket_id: str, data: Classification, db: Db):
    """Set the operator's final classification by hand."""
    return found(service.set_classification(db, ticket_id, data))


@router.delete("/{ticket_id}", status_code=204)
def delete_ticket(ticket_id: str, db: Db) -> None:
    """Delete a ticket with its AI runs, comparisons and labels. Safe to repeat."""
    try:
        tickets.delete_with_dependents(db, ticket_id)
    except PyMongoError:
        log.exception("Deleting ticket %s failed", ticket_id)
        raise HTTPException(
            status_code=500,
            detail="Some of the ticket's records could not be deleted, so the ticket was kept. "
            "Try again.",
        ) from None
