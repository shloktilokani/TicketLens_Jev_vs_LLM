from fastapi.testclient import TestClient

from app.core.settings import Settings
from app.main import create_app
from tests.conftest import TEST_DB


def test_health_reports_process_up(test_settings):
    with TestClient(create_app(test_settings)) as client:
        response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_when_database_is_reachable(test_settings, test_db):
    with TestClient(create_app(test_settings)) as client:
        response = client.get("/api/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready", "database": "ok"}


def test_not_ready_when_database_is_unreachable():
    # Nothing listens on port 9 locally, so the ping fails fast. The URI carries a fake password
    # to prove connection details never reach the response.
    settings = Settings(
        _env_file=None,
        mongodb_uri="mongodb://user:fake-password@127.0.0.1:9",
        mongodb_database=TEST_DB,
    )

    with TestClient(create_app(settings)) as client:
        ready = client.get("/api/health/ready")
        health = client.get("/api/health")

    assert health.status_code == 200
    assert ready.status_code == 503
    body = ready.json()
    assert body["status"] == "unavailable"
    assert body["database"] == "unavailable"
    assert "README" in body["message"]
    assert "fake-password" not in ready.text
