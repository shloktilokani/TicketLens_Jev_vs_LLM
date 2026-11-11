from pathlib import Path

import pytest
from pydantic import ValidationError

from app.core.settings import Settings

ENV_EXAMPLE = Path(__file__).resolve().parents[1] / ".env.example"


def test_defaults_need_no_env_file_or_api_keys(monkeypatch):
    for name in ("MONGODB_URI", "MONGODB_DATABASE", "TYPESAFE_API_KEY", "OPENAI_API_KEY"):
        monkeypatch.delenv(name, raising=False)

    settings = Settings(_env_file=None)

    assert settings.mongodb_uri == "mongodb://127.0.0.1:27017"
    assert settings.mongodb_database == "ticketlens"
    assert settings.api_host == "127.0.0.1"
    assert settings.typesafe_api_key is None
    assert settings.openai_api_key is None


def test_environment_overrides_defaults(monkeypatch):
    monkeypatch.setenv("MONGODB_DATABASE", "other")
    monkeypatch.setenv("BULK_CONCURRENCY", "3")

    settings = Settings(_env_file=None)

    assert settings.mongodb_database == "other"
    assert settings.bulk_concurrency == 3


def test_empty_values_count_as_unset(monkeypatch):
    # A copied .env.example has empty keys; they must read as "not configured", not "".
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("OPENAI_MODEL", "")

    settings = Settings(_env_file=None)

    assert settings.openai_api_key is None
    assert settings.openai_model is None


def test_api_keys_never_appear_in_repr(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-not-a-real-key")

    settings = Settings(_env_file=None)

    assert "sk-test-not-a-real-key" not in repr(settings)
    assert settings.openai_api_key.get_secret_value() == "sk-test-not-a-real-key"


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("BULK_CONCURRENCY", "0"),
        ("JEV_ESCALATION_THRESHOLD", "1.5"),
        ("PROVIDER_TIMEOUT_SECONDS", "0"),
    ],
)
def test_out_of_range_values_are_rejected(monkeypatch, name, value):
    monkeypatch.setenv(name, value)

    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_env_example_lists_every_setting():
    names = {
        line.split("=", 1)[0]
        for line in ENV_EXAMPLE.read_text().splitlines()
        if "=" in line and not line.startswith("#")
    }

    assert names == {field.upper() for field in Settings.model_fields}
