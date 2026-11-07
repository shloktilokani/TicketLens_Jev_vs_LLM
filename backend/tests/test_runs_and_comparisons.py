import pytest
from fastapi.testclient import TestClient

from app.main import create_app

NEW = {
    "title": "Refund not received",
    "description": "I returned my headphones but the refund has not arrived.",
    "customer_name": "Aarav Mehta",
    "customer_email": "aarav@example.test",
    "submission_channel": "Website",
}


@pytest.fixture
def api(test_settings, test_db):
    settings = test_settings.model_copy(update={"mock_providers": True, "mock_delay_seconds": 0})
    with TestClient(create_app(settings)) as client:
        yield client


def new_ticket(api, **changes) -> str:
    return api.post("/api/tickets", json=NEW | changes).json()["ticket_id"]


def run(api, ticket_id: str, provider: str) -> dict:
    response = api.post(f"/api/tickets/{ticket_id}/runs/{provider}")
    assert response.status_code == 200, response.text
    return response.json()


def compare(api, ticket_id: str, jev: dict, gpt: dict):
    return api.post(
        "/api/comparisons",
        json={
            "ticket_id": ticket_id,
            "jev_execution_id": jev["execution_id"],
            "gpt_execution_id": gpt["execution_id"],
        },
    )


def test_run_endpoint_records_and_returns_the_execution(api, test_db):
    ticket_id = new_ticket(api)

    execution = run(api, ticket_id, "jev")

    assert execution["status"] == "Succeeded"
    assert execution["requested_model"] == "mock-jev"
    assert execution["normalized_result"]["subcategory"] == "Refund Delay"
    assert test_db.ai_executions.count_documents({"ticket_id": ticket_id}) == 1


def test_run_unknown_ticket_or_provider(api):
    assert api.post("/api/tickets/SK-9999/runs/jev").status_code == 404
    assert api.post(f"/api/tickets/{new_ticket(api)}/runs/claude").status_code == 422


def test_run_without_mock_or_key_is_recorded_as_not_configured(test_settings, test_db):
    openai = test_settings.model_copy(update={"llm_backend": "openai"})
    with TestClient(create_app(openai)) as client:
        ticket_id = client.post("/api/tickets", json=NEW).json()["ticket_id"]
        execution = client.post(f"/api/tickets/{ticket_id}/runs/gpt").json()

    assert execution["status"] == "Failed"
    assert execution["error"]["code"] == "not_configured"


def test_comparison_counts_agreement_and_links_both_runs(api, test_db):
    ticket_id = new_ticket(api)
    jev, gpt = run(api, ticket_id, "jev"), run(api, ticket_id, "gpt")

    response = compare(api, ticket_id, jev, gpt)

    body = response.json()
    assert response.status_code == 201
    assert body["status"] == "Completed"
    assert body["comparable_field_count"] == 5
    assert body["agreement_count"] == sum(f["match"] for f in body["field_comparison"].values())
    assert body["agreement_rate"] == body["agreement_count"] / 5
    assert set(body["field_comparison"]) == {
        "category",
        "subcategory",
        "priority",
        "sentiment",
        "escalation_required",
    }
    assert "winner" not in str(body).lower()
    linked = test_db.ai_executions.count_documents({"comparison_id": body["comparison_id"]})
    assert linked == 2
    assert test_db.comparisons.count_documents({"ticket_id": ticket_id}) == 1


def test_comparison_is_partial_when_one_provider_fails(api):
    ticket_id = new_ticket(api)
    jev = run(api, ticket_id, "jev")
    api.patch(f"/api/tickets/{ticket_id}", json={"title": "Refund [mock-fail]"})
    gpt = run(api, ticket_id, "gpt")

    body = compare(api, ticket_id, jev, gpt).json()

    assert gpt["status"] == "Failed"
    assert body["status"] == "Partial"
    assert body["comparable_field_count"] == 0
    assert body["agreement_rate"] is None
    assert body["field_comparison"]["category"] == {
        "jev": "Returns & Refunds",
        "gpt": None,
        "match": None,
    }


def test_comparison_is_unavailable_when_both_fail(api):
    ticket_id = new_ticket(api, title="Broken [mock-timeout]")
    jev, gpt = run(api, ticket_id, "jev"), run(api, ticket_id, "gpt")

    assert compare(api, ticket_id, jev, gpt).json()["status"] == "Unavailable"


def test_comparison_rejects_mismatched_runs(api):
    first, second = new_ticket(api), new_ticket(api)
    jev, gpt = run(api, first, "jev"), run(api, second, "gpt")

    assert compare(api, first, jev, gpt).status_code == 422  # GPT run belongs to another ticket
    assert compare(api, first, jev, jev).status_code == 422  # not a GPT run
    missing = {"execution_id": "exec_missing"}
    assert compare(api, first, jev, missing).status_code == 404


def test_comparison_waits_for_running_executions(api, test_db):
    ticket_id = new_ticket(api)
    jev, gpt = run(api, ticket_id, "jev"), run(api, ticket_id, "gpt")
    test_db.ai_executions.update_one(
        {"execution_id": gpt["execution_id"]}, {"$set": {"status": "Running"}}
    )

    assert compare(api, ticket_id, jev, gpt).status_code == 409
