"""MongoDB access for evaluation labels.

Never read by provider request-building code: labels are compared with results only after a run.
"""

from pymongo.database import Database


def insert(db: Database, doc: dict) -> None:
    db.evaluation_labels.insert_one(dict(doc))


def expected_by_ticket(db: Database) -> dict[str, dict]:
    """Every labelled ticket's expected answer. For scoring finished runs only."""
    docs = db.evaluation_labels.find({}, {"_id": 0, "ticket_id": 1, "expected": 1})
    return {doc["ticket_id"]: doc["expected"] for doc in docs}
