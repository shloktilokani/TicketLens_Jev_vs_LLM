from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient
from pymongo.collection import Collection
from pymongo.errors import PyMongoError

from app.core.settings import Settings
from app.main import create_app
from app.repositories.tickets import next_ticket_id
from tests.conftest import TEST_DB

NEW = {
    "title": "Refund not received",
    "description": "I returned my headphones last week but the refund has not arrived.",
    "customer_name": "Aarav Mehta",
    "customer_email": "aarav@example.test",
    "order_id": "ORD-2026-10001",
    "product_name": "Wireless Headphones",
    "submission_channel": "Website",
}
CLASSIFICATION = {
    "category": "Returns & Refunds",
    "subcategory": "Refund Delay",
    "priority": "Medium",
    "sentiment": "Negative",
    "escalation_required": False,
}


@pytest.fixture
def api(test_settings, test_db):
    with TestClient(create_app(test_settings)) as client:
        yield client


def create(api, **changes) -> dict:
    response = api.post("/api/tickets", json=NEW | changes)
    assert response.status_code == 201, response.text
    return response.json()


def classify(api, ticket_id: str, **changes) -> dict:
    response = api.put(
        f"/api/tickets/{ticket_id}/final-classification", json=CLASSIFICATION | changes
    )
    assert response.status_code == 200, response.text
    return response.json()


def ids(response) -> list[str]:
    return [t["ticket_id"] for t in response.json()["items"]]


# --- create and read -----------------------------------------------------------------------


def test_create_assigns_sequential_ids_and_defaults(api):
    first, second = create(api), create(api)

    assert (first["ticket_id"], second["ticket_id"]) == ("SK-1001", "SK-1002")
    assert first["status"] == "Open"
    assert first["customer"] == {"name": "Aarav Mehta", "email": "aarav@example.test"}
    assert first["order"] == {"order_id": "ORD-2026-10001", "product_name": "Wireless Headphones"}
    assert first["source"]["type"] == "manual"
    assert first["final_classification"] is None
    assert first["created_at"] == first["updated_at"]


def test_ids_stay_unique_under_concurrent_creation(test_db):
    with ThreadPoolExecutor(max_workers=8) as pool:
        allocated = list(pool.map(lambda _: next_ticket_id(test_db), range(40)))

    assert len(set(allocated)) == 40
    assert sorted(int(i.removeprefix("SK-")) for i in allocated) == list(range(1001, 1041))


def test_get_returns_ticket_or_404(api):
    ticket = create(api)

    assert api.get(f"/api/tickets/{ticket['ticket_id']}").json() == ticket
    assert api.get("/api/tickets/SK-9999").status_code == 404


def test_invalid_input_is_rejected(api):
    assert api.post("/api/tickets", json=NEW | {"customer_email": "nope"}).status_code == 422


def test_ticket_text_is_kept_exactly(api):
    description = "Line one.\n\n  Line two, exactly as typed.  "

    ticket = create(api, description=description)

    assert api.get(f"/api/tickets/{ticket['ticket_id']}").json()["description"] == description


# --- update, notes, classification ---------------------------------------------------------


def test_update_changes_only_given_fields(api):
    ticket = create(api)

    response = api.patch(
        f"/api/tickets/{ticket['ticket_id']}",
        json={"title": "Refund still missing", "status": "In Progress", "order_id": None},
    )

    updated = response.json()
    assert response.status_code == 200
    assert updated["title"] == "Refund still missing"
    assert updated["status"] == "In Progress"
    assert updated["order"]["order_id"] is None
    assert updated["order"]["product_name"] == "Wireless Headphones"
    assert updated["customer"]["name"] == "Aarav Mehta"
    assert updated["updated_at"] > ticket["updated_at"]


@pytest.mark.parametrize(
    "change", [{"title": None}, {"status": "Done"}, {"customer_email": "bad"}, {}]
)
def test_invalid_updates_are_rejected(api, change):
    ticket = create(api)

    assert api.patch(f"/api/tickets/{ticket['ticket_id']}", json=change).status_code == 422


def test_update_unknown_ticket_is_404(api):
    assert api.patch("/api/tickets/SK-9999", json={"title": "x"}).status_code == 404


def test_notes_are_appended(api):
    ticket = create(api)

    api.post(f"/api/tickets/{ticket['ticket_id']}/notes", json={"text": "Called the courier."})
    response = api.post(f"/api/tickets/{ticket['ticket_id']}/notes", json={"text": "Refund sent."})

    notes = response.json()["operator_notes"]
    assert response.status_code == 201
    assert [n["text"] for n in notes] == ["Called the courier.", "Refund sent."]
    assert notes[0]["note_id"] != notes[1]["note_id"]
    assert (
        api.post(f"/api/tickets/{ticket['ticket_id']}/notes", json={"text": " "}).status_code == 422
    )


def test_manual_classification_is_stored_with_version(api):
    ticket = create(api)

    final = classify(api, ticket["ticket_id"])["final_classification"]

    assert final["subcategory"] == "Refund Delay"
    assert final["manually_edited"] is True
    assert final["selected_from_execution_id"] is None
    assert final["taxonomy_version"] == "1.0"


def test_inconsistent_classification_is_rejected(api):
    ticket = create(api)

    response = api.put(
        f"/api/tickets/{ticket['ticket_id']}/final-classification",
        json=CLASSIFICATION | {"subcategory": "Password Reset"},
    )

    assert response.status_code == 422
    assert api.get(f"/api/tickets/{ticket['ticket_id']}").json()["final_classification"] is None


# --- search, filters, sort, pagination -----------------------------------------------------


@pytest.mark.parametrize(
    "query", ["SK-1002", "laptop", "LAPTOP", "Diya", "diya@example.test", "ORD-77"]
)
def test_search_matches_each_searchable_field(api, query):
    create(api)
    create(
        api,
        title="Laptop screen cracked",
        customer_name="Diya Shah",
        customer_email="diya@example.test",
        order_id="ORD-77",
    )

    assert ids(api.get("/api/tickets", params={"q": query})) == ["SK-1002"]


def test_search_treats_input_as_plain_text(api):
    create(api)

    response = api.get("/api/tickets", params={"q": ".*("})

    assert response.status_code == 200
    assert response.json()["total"] == 0


def test_filters_by_status_category_and_priority(api):
    a, b, c = create(api), create(api), create(api)
    classify(api, a["ticket_id"], priority="High")
    classify(
        api,
        b["ticket_id"],
        category="Account & Login",
        subcategory="Password Reset",
        priority="High",
    )
    api.patch(f"/api/tickets/{c['ticket_id']}", json={"status": "Resolved"})

    assert ids(api.get("/api/tickets", params={"status": "Resolved"})) == ["SK-1003"]
    assert ids(api.get("/api/tickets", params={"category": "Account & Login"})) == ["SK-1002"]
    assert ids(
        api.get("/api/tickets", params={"priority": "High", "sort": "created_at", "order": "asc"})
    ) == ["SK-1001", "SK-1002"]
    assert api.get("/api/tickets", params={"priority": "Urgent"}).status_code == 422


def test_sorts_by_created_date(api):
    for _ in range(3):
        create(api)

    assert ids(api.get("/api/tickets")) == ["SK-1003", "SK-1002", "SK-1001"]
    assert ids(api.get("/api/tickets", params={"order": "asc"})) == [
        "SK-1001",
        "SK-1002",
        "SK-1003",
    ]


def test_sorts_by_priority_most_urgent_first_unclassified_last(api):
    for _ in range(4):
        create(api)
    classify(api, "SK-1001", priority="Low")
    classify(api, "SK-1002", priority="Critical")
    classify(api, "SK-1004", priority="Medium")

    assert ids(api.get("/api/tickets", params={"sort": "priority"})) == [
        "SK-1002",
        "SK-1004",
        "SK-1001",
        "SK-1003",
    ]
    assert ids(api.get("/api/tickets", params={"sort": "priority", "order": "asc"}))[:3] == [
        "SK-1001",
        "SK-1004",
        "SK-1002",
    ]


def test_pagination_is_bounded(api):
    for _ in range(5):
        create(api)

    page = api.get("/api/tickets", params={"page": 2, "page_size": 2, "order": "asc"}).json()

    assert [t["ticket_id"] for t in page["items"]] == ["SK-1003", "SK-1004"]
    assert (page["total"], page["page"], page["page_size"]) == (5, 2, 2)
    assert api.get("/api/tickets", params={"page_size": 101}).status_code == 422
    assert api.get("/api/tickets", params={"page": 0}).status_code == 422


# --- delete --------------------------------------------------------------------------------


def seed_dependents(db, ticket_id: str) -> None:
    db.comparisons.insert_one({"comparison_id": f"cmp_{ticket_id}", "ticket_id": ticket_id})
    db.ai_executions.insert_one({"execution_id": f"exec_{ticket_id}", "ticket_id": ticket_id})
    db.evaluation_labels.insert_one({"ticket_id": ticket_id})


def test_delete_removes_ticket_and_its_dependents_only(api, test_db):
    keep, gone = create(api), create(api)
    for t in (keep, gone):
        seed_dependents(test_db, t["ticket_id"])

    response = api.delete(f"/api/tickets/{gone['ticket_id']}")

    assert response.status_code == 204
    assert api.get(f"/api/tickets/{gone['ticket_id']}").status_code == 404
    for name in ("comparisons", "ai_executions", "evaluation_labels"):
        assert test_db[name].count_documents({"ticket_id": gone["ticket_id"]}) == 0
        assert test_db[name].count_documents({"ticket_id": keep["ticket_id"]}) == 1
    assert api.get(f"/api/tickets/{keep['ticket_id']}").status_code == 200


def test_repeated_delete_is_safe(api):
    ticket = create(api)

    assert api.delete(f"/api/tickets/{ticket['ticket_id']}").status_code == 204
    assert api.delete(f"/api/tickets/{ticket['ticket_id']}").status_code == 204


def test_failed_dependent_delete_keeps_the_ticket(api, test_db, monkeypatch):
    ticket = create(api)
    seed_dependents(test_db, ticket["ticket_id"])
    original = Collection.delete_many

    def failing_delete_many(self, *args, **kwargs):
        if self.name == "ai_executions":
            raise PyMongoError("simulated failure")
        return original(self, *args, **kwargs)

    monkeypatch.setattr(Collection, "delete_many", failing_delete_many)
    response = api.delete(f"/api/tickets/{ticket['ticket_id']}")
    monkeypatch.undo()

    assert response.status_code == 500
    assert "kept" in response.json()["detail"]
    assert api.get(f"/api/tickets/{ticket['ticket_id']}").status_code == 200
    # A retry, once the database recovers, finishes the job.
    assert api.delete(f"/api/tickets/{ticket['ticket_id']}").status_code == 204
    assert test_db.ai_executions.count_documents({"ticket_id": ticket["ticket_id"]}) == 0


def test_ticket_endpoints_explain_when_database_is_down():
    settings = Settings(
        _env_file=None, mongodb_uri="mongodb://127.0.0.1:9", mongodb_database=TEST_DB
    )

    with TestClient(create_app(settings)) as client:
        response = client.get("/api/tickets")

    assert response.status_code == 503
    assert "README" in response.json()["detail"]
