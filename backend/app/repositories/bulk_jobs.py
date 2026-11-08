"""MongoDB access for bulk job progress."""

from pymongo import ReturnDocument
from pymongo.database import Database

from app.core.taxonomy import BulkJobStatus

ACTIVE = [BulkJobStatus.QUEUED, BulkJobStatus.RUNNING]
NO_ID = {"_id": 0}


def insert(db: Database, doc: dict) -> None:
    db.bulk_jobs.insert_one(dict(doc))  # a copy: insert_one adds an ObjectId _id


def get(db: Database, job_id: str) -> dict | None:
    return db.bulk_jobs.find_one({"job_id": job_id}, NO_ID)


def newest_first(db: Database, limit: int) -> list[dict]:
    return list(db.bulk_jobs.find({}, NO_ID).sort([("created_at", -1), ("_id", -1)]).limit(limit))


def count(db: Database) -> int:
    return db.bulk_jobs.count_documents({})


def has_active(db: Database) -> bool:
    return db.bulk_jobs.count_documents({"status": {"$in": ACTIVE}}, limit=1) > 0


def update(db: Database, job_id: str, changes: dict) -> dict | None:
    return db.bulk_jobs.find_one_and_update(
        {"job_id": job_id},
        {"$set": changes},
        projection=NO_ID,
        return_document=ReturnDocument.AFTER,
    )


def record_outcome(db: Database, job_id: str, outcome: dict, counter: str) -> None:
    """One attempt's result. $push and $inc are atomic, so parallel workers cannot lose counts."""
    db.bulk_jobs.update_one(
        {"job_id": job_id}, {"$push": {"outcomes": outcome}, "$inc": {counter: 1}}
    )


def mark_active_interrupted(db: Database, changes: dict) -> None:
    db.bulk_jobs.update_many(
        {"status": {"$in": ACTIVE}}, {"$set": {"status": BulkJobStatus.INTERRUPTED} | changes}
    )
