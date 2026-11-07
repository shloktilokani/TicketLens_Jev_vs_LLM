"""MongoDB access for tickets and the ticket-ID counter."""

import re
from typing import Literal

from pymongo import ReturnDocument
from pymongo.database import Database

from app.core.taxonomy import Priority

FIRST_TICKET_NUMBER = 1001  # SK-1001 (requirements.md section 4)
PRIORITY_ORDER = [p.value for p in Priority]  # most urgent first
SEARCH_FIELDS = ("ticket_id", "title", "customer.name", "customer.email", "order.order_id")
DEPENDENT_COLLECTIONS = ("comparisons", "ai_executions", "evaluation_labels")
NO_ID = {"_id": 0}


def next_ticket_id(db: Database) -> str:
    # $inc with upsert is atomic, and MongoDB retries a racing first-time upsert on _id itself.
    # IDs are never reused; a failed insert can leave a gap, which is acceptable.
    counter = db.counters.find_one_and_update(
        {"_id": "ticket_id"},
        {"$inc": {"issued": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    return f"SK-{FIRST_TICKET_NUMBER - 1 + counter['issued']}"


def insert(db: Database, doc: dict) -> None:
    db.tickets.insert_one(dict(doc))  # a copy: insert_one adds an ObjectId _id to what it is given


def get(db: Database, ticket_id: str) -> dict | None:
    return db.tickets.find_one({"ticket_id": ticket_id}, NO_ID)


def fingerprint_exists(db: Database, fingerprint: str) -> bool:
    return db.tickets.count_documents({"source.source_fingerprint": fingerprint}, limit=1) > 0


def update(db: Database, ticket_id: str, operations: dict) -> dict | None:
    """Apply MongoDB update operators; return the updated ticket, or None if it does not exist."""
    return db.tickets.find_one_and_update(
        {"ticket_id": ticket_id},
        operations,
        projection=NO_ID,
        return_document=ReturnDocument.AFTER,
    )


def delete_with_dependents(db: Database, ticket_id: str) -> None:
    """Delete dependents first and the ticket last (data-model.md section 9).

    Standalone MongoDB has no multi-document transactions. If any step raises, the ticket is
    still there and a retry finishes the job. Deleting a missing ticket is a harmless no-op.
    """
    for name in DEPENDENT_COLLECTIONS:
        db[name].delete_many({"ticket_id": ticket_id})
    db.tickets.delete_one({"ticket_id": ticket_id})


def search(
    db: Database,
    *,
    q: str | None,
    filters: dict[str, str | None],
    sort: Literal["created_at", "priority"],
    descending: bool,
    page: int,
    page_size: int,
) -> tuple[list[dict], int]:
    """One page of tickets plus the total match count. `filters` maps document paths to values."""
    query: dict = {path: value for path, value in filters.items() if value is not None}
    if q:
        # re.escape: the search box is plain text, never a regular expression.
        pattern = {"$regex": re.escape(q), "$options": "i"}
        query["$or"] = [{field: pattern} for field in SEARCH_FIELDS]

    stages: list[dict] = [{"$match": query}]
    if sort == "priority":
        rank = {"$indexOfArray": [PRIORITY_ORDER, "$final_classification.priority"]}
        stages.append({"$addFields": {"_rank": rank, "_unranked": {"$eq": [rank, -1]}}})
        # Unclassified tickets come last in both directions; "desc" means most urgent first.
        order = {"_unranked": 1, "_rank": 1 if descending else -1, "created_at": -1, "_id": -1}
    else:
        direction = -1 if descending else 1
        order = {"created_at": direction, "_id": direction}
    stages += [
        {"$sort": order},
        {"$skip": (page - 1) * page_size},
        {"$limit": page_size},
        {"$project": {"_id": 0, "_rank": 0, "_unranked": 0}},
    ]
    return list(db.tickets.aggregate(stages)), db.tickets.count_documents(query)
