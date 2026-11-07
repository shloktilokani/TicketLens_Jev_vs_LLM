"""MongoDB access for AI execution records."""

from pymongo import ReturnDocument
from pymongo.database import Database


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
