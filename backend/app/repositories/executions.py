"""MongoDB access for AI execution records."""

from datetime import UTC, date, datetime, time, timedelta

from pymongo import ReturnDocument
from pymongo.database import Database

from app.core.taxonomy import ExecutionStatus

LIST_PROJECTION = {
    "_id": 0,
    "input_snapshot": 0,
    "request_payload_redacted": 0,
    "response_payload_redacted": 0,
}


def insert(db: Database, doc: dict) -> None:
    db.ai_executions.insert_one(dict(doc))  # a copy: insert_one adds an ObjectId _id


def update(db: Database, execution_id: str, changes: dict) -> dict:
    return db.ai_executions.find_one_and_update(
        {"execution_id": execution_id},
        {"$set": changes},
        projection={"_id": 0},
        return_document=ReturnDocument.AFTER,
    )


def get(db: Database, execution_id: str) -> dict | None:
    return db.ai_executions.find_one({"execution_id": execution_id}, {"_id": 0})


def link_comparison(db: Database, execution_ids: list[str], comparison_id: str) -> None:
    db.ai_executions.update_many(
        {"execution_id": {"$in": execution_ids}}, {"$set": {"comparison_id": comparison_id}}
    )


def succeeded_ticket_ids(db: Database, provider: str, model: str, ticket_ids: list[str]) -> set:
    """Which of these tickets already have a successful run of this side on this model."""
    return set(
        db.ai_executions.distinct(
            "ticket_id",
            {
                "ticket_id": {"$in": ticket_ids},
                "provider": provider,
                "requested_model": model,
                "status": ExecutionStatus.SUCCEEDED,
            },
        )
    )


def cancel_running(db: Database, now: datetime, message: str) -> None:
    """Close records left Running by a restart, so no attempt stays in limbo forever."""
    db.ai_executions.update_many(
        {"status": ExecutionStatus.RUNNING},
        {
            "$set": {
                "status": ExecutionStatus.CANCELLED,
                "completed_at": now,
                "error": {"code": "interrupted", "http_status": None, "message": message},
            }
        },
    )


def latest_finished_real(db: Database, ticket_ids: list[str]) -> dict[tuple[str, str], dict]:
    """Each side's newest finished run per ticket, leaving out fake-provider runs."""
    stages = [
        {
            "$match": {
                "ticket_id": {"$in": ticket_ids},
                "status": {"$ne": ExecutionStatus.RUNNING},
                "requested_model": {"$not": {"$regex": "^mock-"}},
            }
        },
        {"$sort": {"started_at": -1, "_id": -1}},
        {
            "$group": {
                "_id": {"ticket_id": "$ticket_id", "provider": "$provider"},
                "status": {"$first": "$status"},
                "normalized_result": {"$first": "$normalized_result"},
                "requested_model": {"$first": "$requested_model"},
            }
        },
    ]
    latest = {}
    for doc in db.ai_executions.aggregate(stages):
        key = doc.pop("_id")
        latest[(key["ticket_id"], key["provider"])] = doc
    return latest


def latest_by_ticket(db: Database, ticket_ids: list[str]) -> dict[str, dict]:
    """Each ticket's most recent run: {ticket_id: {provider, status, started_at}}."""
    stages = [
        {"$match": {"ticket_id": {"$in": ticket_ids}}},
        {"$sort": {"started_at": -1}},
        {
            "$group": {
                "_id": "$ticket_id",
                "provider": {"$first": "$provider"},
                "status": {"$first": "$status"},
                "started_at": {"$first": "$started_at"},
            }
        },
    ]
    return {d.pop("_id"): d for d in db.ai_executions.aggregate(stages)}


def search(
    db: Database,
    *,
    filters: dict[str, str | None],
    date_from: date | None,
    date_to: date | None,
    page: int,
    page_size: int,
) -> tuple[list[dict], int]:
    """One page of runs, newest first, without payloads, plus the total match count."""
    query: dict = {field: value for field, value in filters.items() if value is not None}
    started: dict = {}
    if date_from:
        started["$gte"] = datetime.combine(date_from, time.min, UTC)
    if date_to:  # the whole of that day, in UTC
        started["$lt"] = datetime.combine(date_to + timedelta(days=1), time.min, UTC)
    if started:
        query["started_at"] = started
    cursor = (
        db.ai_executions.find(query, LIST_PROJECTION)
        .sort([("started_at", -1), ("_id", -1)])
        .skip((page - 1) * page_size)
        .limit(page_size)
    )
    return list(cursor), db.ai_executions.count_documents(query)
