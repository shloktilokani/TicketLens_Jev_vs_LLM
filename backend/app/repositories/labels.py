"""MongoDB access for evaluation labels.

Never read by provider request-building code: labels are compared with results only after a run.
"""

from pymongo.database import Database


def insert(db: Database, doc: dict) -> None:
    db.evaluation_labels.insert_one(dict(doc))
