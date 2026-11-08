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


def compared(api, title="Refund not received") -> dict:
    """Create a ticket, run both fake providers and compare. Returns the comparison."""
    ticket_id = api.post("/api/tickets", json=NEW | {"title": title}).json()["ticket_id"]
    jev = api.post(f"/api/tickets/{ticket_id}/runs/jev").json()
    llm = api.post(f"/api/tickets/{ticket_id}/runs/gpt").json()
    return api.post(
        "/api/comparisons",
        json={
            "ticket_id": ticket_id,
            "jev_execution_id": jev["execution_id"],
            "gpt_execution_id": llm["execution_id"],
        },
    ).json()


def make_real(db, comparison: dict) -> None:
    """Relabel a fake comparison's runs as if real models produced them."""
    for key, model in (("jev_execution_id", "autotrust-jev:9b"), ("gpt_execution_id", "qwen3:8b")):
        db.ai_executions.update_one(
            {"execution_id": comparison[key]},
            {"$set": {"requested_model": model, "actual_model": model}},
        )


def test_dashboard_is_empty_before_any_runs(api):
    body = api.get("/api/dashboard").json()

    assert body["tickets"] == {"total": 0, "by_status": {}}
    assert body["metrics"] is None
    assert body["real_comparisons"] == 0


def test_dashboard_counts_real_runs_and_excludes_fake_ones(api, test_db):
    make_real(test_db, compared(api))
    compared(api, "Stays fake")

    body = api.get("/api/dashboard").json()

    assert body["real_comparisons"] == 1
    assert body["fake_comparisons_excluded"] == 1
    assert body["tickets"] == {"total": 2, "by_status": {"Open": 2}}
    assert body["metrics"]["tickets"] == 1
    assert body["metrics"]["per_field"]["category"]["compared"] == 1
    assert body["models"] == {"jev": ["autotrust-jev:9b"], "llm": ["qwen3:8b"]}


def test_comparison_list_is_newest_first_and_flags_fake_runs(api, test_db):
    first = compared(api, "First")
    second = compared(api, "Second")
    make_real(test_db, first)

    body = api.get("/api/comparisons").json()

    assert [c["comparison_id"] for c in body["items"]] == [
        second["comparison_id"],
        first["comparison_id"],
    ]
    newest, oldest = body["items"]
    assert (newest["title"], newest["fake"]) == ("Second", True)
    assert (oldest["title"], oldest["fake"], oldest["jev_model"]) == (
        "First",
        False,
        "autotrust-jev:9b",
    )
    assert oldest["llm_ms"] is not None
    assert body["total"] == 2
    assert api.get("/api/comparisons", params={"limit": 1}).json()["items"][0]["title"] == "Second"
    assert api.get("/api/comparisons", params={"limit": 1001}).status_code == 422


def test_comparison_detail_returns_both_stored_runs(api):
    comparison = compared(api)

    body = api.get(f"/api/comparisons/{comparison['comparison_id']}").json()

    assert body["comparison"]["comparison_id"] == comparison["comparison_id"]
    assert body["jev"]["provider"] == "jev"
    assert body["llm"]["normalized_result"]["summary"]
    assert body["ticket"]["title"] == "Refund not received"
    assert api.get("/api/comparisons/cmp_missing").status_code == 404


def test_ticket_list_shows_each_tickets_latest_run(api):
    run_ticket = compared(api, "Has runs")["ticket_id"]
    api.post("/api/tickets", json=NEW | {"title": "No runs"})

    items = {t["ticket_id"]: t for t in api.get("/api/tickets").json()["items"]}

    assert items[run_ticket]["latest_run"]["status"] == "Succeeded"
    other = next(t for t in items.values() if t["ticket_id"] != run_ticket)
    assert other["latest_run"] is None


def test_comparisons_can_be_listed_for_one_ticket(api):
    wanted = compared(api)
    compared(api, title="Another ticket")

    listed = api.get(f"/api/comparisons?ticket_id={wanted['ticket_id']}").json()

    assert listed["total"] == 1
    assert [c["comparison_id"] for c in listed["items"]] == [wanted["comparison_id"]]
