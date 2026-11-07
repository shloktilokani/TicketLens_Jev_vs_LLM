"""MongoDB access for Jev-vs-GPT comparison records."""

from pymongo.database import Database


def insert(db: Database, doc: dict) -> None:
    db.comparisons.insert_one(dict(doc))  # a copy: insert_one adds an ObjectId _id
