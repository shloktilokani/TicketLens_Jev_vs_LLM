from fastapi.testclient import TestClient

from app.main import app


def test_swagger_ui_is_served() -> None:
    response = TestClient(app).get("/docs")

    assert response.status_code == 200
    assert "swagger" in response.text.lower()


def test_openapi_schema_names_the_app() -> None:
    response = TestClient(app).get("/openapi.json")

    assert response.status_code == 200
    assert response.json()["info"]["title"] == "TicketLens API"
