from fastapi.testclient import TestClient

from app.main import create_app


def preflight(client, origin: str):
    return client.options(
        "/api/tickets",
        headers={"Origin": origin, "Access-Control-Request-Method": "POST"},
    )


def test_cors_allows_only_the_configured_frontend_origin(test_settings):
    with TestClient(create_app(test_settings)) as client:
        allowed = preflight(client, "http://localhost:5173")
        other = preflight(client, "http://evil.example")

    assert allowed.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert "access-control-allow-origin" not in other.headers


def test_provider_status_reports_configured_without_revealing_keys(test_settings):
    settings = test_settings.model_copy(
        update={
            "typesafe_api_key": "ts-secret-value",
            "openai_api_key": None,
            "llm_backend": "openai",
        }
    )

    with TestClient(create_app(settings)) as client:
        response = client.get("/api/providers/status")

    body = response.json()
    assert (body["jev"]["configured"], body["gpt"]["configured"]) == (True, False)
    assert body["jev"]["label"] == "TypeSafe Jev · jev-latest"
    assert "ts-secret-value" not in response.text
