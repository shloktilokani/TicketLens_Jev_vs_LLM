import pytest
from pymongo import MongoClient

from app.core import taxonomy
from app.core.settings import Settings
from app.providers import http

TEST_DB = "ticketlens_test"


@pytest.fixture(autouse=True)
def default_taxonomy():
    """The active taxonomy lives in the process, so no test may leak its changes to another."""
    taxonomy.reset()
    yield
    taxonomy.reset()


@pytest.fixture(autouse=True)
def no_retry_waits(monkeypatch):
    """Retries still happen in tests; only the waiting between them is skipped."""
    monkeypatch.setattr(http, "pause", lambda seconds: None)


@pytest.fixture
def test_settings() -> Settings:
    # _env_file=None keeps tests independent of a developer's real backend/.env.
    return Settings(_env_file=None, mongodb_database=TEST_DB)


@pytest.fixture
def test_db(test_settings):
    """A throwaway database, emptied before and after each test. Skips if MongoDB is down."""
    client = MongoClient(test_settings.mongodb_uri, serverSelectionTimeoutMS=2000)
    try:
        client.admin.command("ping")
    except Exception:
        client.close()
        pytest.skip("MongoDB is not running at the configured MONGODB_URI")
    client.drop_database(TEST_DB)
    yield client[TEST_DB]
    client.drop_database(TEST_DB)
    client.close()
