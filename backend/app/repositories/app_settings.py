"""MongoDB access for the one active settings document. API keys are never stored here."""

from pymongo import ReturnDocument
from pymongo.database import Database

ACTIVE = "active"


def get(db: Database) -> dict:
    return db.app_settings.find_one({"_id": ACTIVE}) or {}


def update(db: Database, operations: dict) -> dict:
    return db.app_settings.find_one_and_update(
        {"_id": ACTIVE}, operations, upsert=True, return_document=ReturnDocument.AFTER
    )


def labels_in_use(db: Database) -> set[tuple[str, str]]:
    """Every category and subcategory pair a stored record relies on."""
    sources = (
        ("tickets", "final_classification"),
        ("ai_executions", "normalized_result"),
        ("evaluation_labels", "expected"),
    )
    used = set()
    for collection, field in sources:
        stages = [
            {"$match": {field: {"$ne": None}}},
            {"$group": {"_id": {"c": f"${field}.category", "s": f"${field}.subcategory"}}},
        ]
        used |= {(d["_id"]["c"], d["_id"]["s"]) for d in db[collection].aggregate(stages)}
    return used
