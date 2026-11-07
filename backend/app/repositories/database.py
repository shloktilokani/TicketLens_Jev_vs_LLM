"""MongoDB access: the client, a readiness ping, and index setup (data-model.md section 8)."""

from pymongo import ASCENDING, DESCENDING, MongoClient
from pymongo.database import Database
from pymongo.errors import PyMongoError

from app.core.settings import Settings

# Fail fast when MongoDB is down, instead of PyMongo's 30-second default.
SERVER_SELECTION_TIMEOUT_MS = 2000

# Shown to the operator; never includes the URI, which may contain credentials.
DB_UNAVAILABLE_MESSAGE = (
    "MongoDB is not reachable. Start it (see README.md, 'Run locally'), "
    "then check MONGODB_URI in backend/.env."
)

INDEXES: dict[str, list[tuple[list[tuple[str, int]], dict]]] = {
    "tickets": [
        ([("ticket_id", ASCENDING)], {"unique": True}),
        ([("created_at", DESCENDING)], {}),
        ([("status", ASCENDING)], {}),
        ([("final_classification.category", ASCENDING)], {}),
        # Only imported tickets have a fingerprint; the partial filter keeps the rest out of the
        # unique index.
        (
            [("source.source_fingerprint", ASCENDING)],
            {
                "unique": True,
                "partialFilterExpression": {"source.source_fingerprint": {"$type": "string"}},
            },
        ),
    ],
    "ai_executions": [
        ([("execution_id", ASCENDING)], {"unique": True}),
        ([("ticket_id", ASCENDING), ("started_at", DESCENDING)], {}),
        ([("provider", ASCENDING), ("started_at", DESCENDING)], {}),
    ],
    "comparisons": [
        ([("comparison_id", ASCENDING)], {"unique": True}),
        ([("ticket_id", ASCENDING), ("created_at", DESCENDING)], {}),
    ],
    "evaluation_labels": [([("ticket_id", ASCENDING)], {"unique": True})],
    "bulk_jobs": [([("job_id", ASCENDING)], {"unique": True})],
}


def connect(settings: Settings) -> MongoClient:
    """Create the client. Connecting is lazy, so the app still starts when MongoDB is down."""
    return MongoClient(
        settings.mongodb_uri,
        serverSelectionTimeoutMS=SERVER_SELECTION_TIMEOUT_MS,
        tz_aware=True,
    )


def is_reachable(client: MongoClient) -> bool:
    try:
        client.admin.command("ping")
    except PyMongoError:
        return False
    return True


def ensure_indexes(db: Database) -> None:
    """Create every index. Safe to run repeatedly: MongoDB skips indexes that already exist."""
    for collection, specs in INDEXES.items():
        for keys, options in specs:
            db[collection].create_index(keys, **options)


def find_all(db: Database, collection: str, sort_field: str) -> list[dict]:
    """Every document in a collection, oldest first, without internal ids (used by exports)."""
    return list(db[collection].find({}, {"_id": 0}).sort(sort_field, ASCENDING))


def find_in(db: Database, collection: str, field: str, values: list[str]) -> list[dict]:
    """Documents whose `field` is one of `values`, without internal ids (used by run reports)."""
    return list(db[collection].find({field: {"$in": list(values)}}, {"_id": 0}))
