import pytest

from app.core.settings import get_settings
from app.repositories.database import ensure_indexes
from scripts import init_db
from tests.conftest import TEST_DB

UNIQUE_KEYS = [
    ("tickets", "ticket_id"),
    ("ai_executions", "execution_id"),
    ("comparisons", "comparison_id"),
    ("evaluation_labels", "ticket_id"),
    ("bulk_jobs", "job_id"),
]


def keys_of(collection) -> dict[tuple, dict]:
    return {tuple(info["key"]): info for info in collection.index_information().values()}


def test_indexes_are_created_and_safe_to_rerun(test_db):
    ensure_indexes(test_db)
    ensure_indexes(test_db)

    for collection, field in UNIQUE_KEYS:
        assert keys_of(test_db[collection])[((field, 1),)]["unique"] is True

    fingerprint = keys_of(test_db.tickets)[(("source.source_fingerprint", 1),)]
    assert fingerprint["unique"] is True
    assert "partialFilterExpression" in fingerprint
    assert (("ticket_id", 1), ("started_at", -1)) in keys_of(test_db.ai_executions)


def test_tickets_without_fingerprint_do_not_collide(test_db):
    ensure_indexes(test_db)

    test_db.tickets.insert_many([{"ticket_id": "SK-1"}, {"ticket_id": "SK-2"}])

    assert test_db.tickets.count_documents({}) == 2


@pytest.fixture
def init_db_settings(monkeypatch):
    def use(uri: str) -> None:
        monkeypatch.setenv("MONGODB_URI", uri)
        monkeypatch.setenv("MONGODB_DATABASE", TEST_DB)
        get_settings.cache_clear()

    yield use
    get_settings.cache_clear()


def test_init_db_script_is_repeatable(test_db, init_db_settings, capsys):
    init_db_settings("mongodb://127.0.0.1:27017")

    assert init_db.main() == 0
    assert init_db.main() == 0
    assert TEST_DB in capsys.readouterr().out


def test_init_db_script_explains_when_database_is_down(init_db_settings, capsys):
    init_db_settings("mongodb://127.0.0.1:9")

    assert init_db.main() == 1
    assert "README" in capsys.readouterr().err
