"""MongoDB access for Jev-vs-GPT comparison records."""

from pymongo.database import Database


def insert(db: Database, doc: dict) -> None:
    db.comparisons.insert_one(dict(doc))  # a copy: insert_one adds an ObjectId _id


def newest_first(db: Database, limit: int = 0, ticket_id: str | None = None) -> list[dict]:
    """Comparisons, newest first, optionally for one ticket. `limit=0` means all."""
    query = {"ticket_id": ticket_id} if ticket_id else {}
    cursor = db.comparisons.find(query, {"_id": 0}).sort([("created_at", -1), ("_id", -1)])
    return list(cursor.limit(limit))


def count(db: Database, ticket_id: str | None = None) -> int:
    return db.comparisons.count_documents({"ticket_id": ticket_id} if ticket_id else {})


def get(db: Database, comparison_id: str) -> dict | None:
    return db.comparisons.find_one({"comparison_id": comparison_id}, {"_id": 0})
