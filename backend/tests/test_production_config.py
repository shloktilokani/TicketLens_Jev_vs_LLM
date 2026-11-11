import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.settings import Settings
from app.main import create_app

SECRET_URI = "mongodb+srv://user:db-password-value@cluster.example.net/ticketlens"
SAFE = {
    "app_env": "production",
    "mongodb_uri": SECRET_URI,
    "frontend_origin": "https://ticketlens.example.test",
    "access_control_confirmed": True,
}


def production(**changes) -> Settings:
    return Settings(_env_file=None, **(SAFE | changes))


def test_a_safe_production_configuration_is_accepted():
    assert production().app_env == "production"


@pytest.mark.parametrize(
    ("changes", "reason"),
    [
        ({"mongodb_uri": "mongodb://127.0.0.1:27017"}, "MONGODB_URI"),
        ({"mongodb_uri": "mongodb://localhost:27017"}, "MONGODB_URI"),
        ({"frontend_origin": "http://ticketlens.example.test"}, "FRONTEND_ORIGIN"),
        ({"frontend_origin": "https://*.example.test"}, "FRONTEND_ORIGIN"),
        ({"mock_providers": True}, "MOCK_PROVIDERS"),
        ({"access_control_confirmed": False}, "ACCESS_CONTROL_CONFIRMED"),
    ],
)
def test_unsafe_production_settings_stop_the_app_starting(changes, reason):
    with pytest.raises(ValidationError) as raised:
        production(**changes)

    assert reason in str(raised.value)


def test_the_demo_is_refused_in_production_by_default():
    """There is no login, so production needs a stated access-control layer in front."""
    with pytest.raises(ValidationError) as raised:
        Settings(
            _env_file=None,
            app_env="production",
            mongodb_uri=SECRET_URI,
            frontend_origin="https://ticketlens.example.test",
        )

    assert "ACCESS_CONTROL_CONFIRMED" in str(raised.value)


def test_development_keeps_its_local_defaults():
    settings = Settings(_env_file=None)

    assert settings.app_env == "development"
    assert settings.mongodb_uri == "mongodb://127.0.0.1:27017"
    assert settings.access_control_confirmed is False


def test_database_credentials_never_appear_in_output_or_errors():
    assert "db-password-value" not in repr(production())
    with pytest.raises(ValidationError) as raised:
        production(mock_providers=True)
    assert "db-password-value" not in str(raised.value)


def test_interactive_api_docs_are_off_in_production_only(test_settings, monkeypatch):
    prod = test_settings.model_copy(update={"app_env": "production"})
    with TestClient(create_app(prod)) as client:
        assert client.get("/docs").status_code == 404
        assert client.get("/openapi.json").status_code == 404
        assert client.get("/api/health").status_code == 200
    with TestClient(create_app(test_settings)) as client:
        assert client.get("/docs").status_code == 200
