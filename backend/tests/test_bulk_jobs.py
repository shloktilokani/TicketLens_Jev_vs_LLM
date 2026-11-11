import threading
import time
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from app.core.taxonomy import BulkJobStatus
from app.jobs import bulk
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


def start(api, **body):
    """Start a job. TestClient finishes background work first, so this returns the end state."""
    response = api.post("/api/bulk-jobs", json=body)
    if response.status_code != 202:
        return response
    return api.get(f"/api/bulk-jobs/{response.json()['job_id']}")


def test_selected_tickets_on_both_sides_are_run_compared_and_counted(api, test_db):
    ids = [new_ticket(api), new_ticket(api)]

    job = start(api, ticket_ids=ids, providers=["jev", "gpt"]).json()

    assert job["status"] == "Completed"
    assert (job["total"], job["completed"], job["failed"], job["skipped"]) == (4, 4, 0, 0)
    assert job["started_at"] and job["completed_at"]
    assert len(job["outcomes"]) == 4
    for ticket_id in ids:
        assert test_db.ai_executions.count_documents({"ticket_id": ticket_id}) == 2
        assert test_db.comparisons.count_documents({"ticket_id": ticket_id}) == 1
    run_ids = {o["execution_id"] for o in job["outcomes"]}
    assert test_db.ai_executions.count_documents({"execution_id": {"$in": list(run_ids)}}) == 4


def test_one_side_runs_alone_with_no_comparison(api, test_db):
    ticket_id = new_ticket(api)

    job = start(api, ticket_ids=[ticket_id], providers=["gpt"]).json()

    assert job["total"] == 1
    assert test_db.ai_executions.count_documents({"ticket_id": ticket_id, "provider": "gpt"}) == 1
    assert test_db.ai_executions.count_documents({"ticket_id": ticket_id, "provider": "jev"}) == 0
    assert test_db.comparisons.count_documents({}) == 0


def test_a_failure_does_not_stop_unrelated_tickets(api):
    bad = new_ticket(api, title="[mock-fail] Broken")
    good = new_ticket(api)

    job = start(api, ticket_ids=[bad, good], providers=["jev"]).json()

    assert job["status"] == "Completed With Errors"
    assert (job["completed"], job["failed"]) == (1, 1)
    assert "1 of 2" in job["error_summary"]
    by_ticket = {o["ticket_id"]: o["status"] for o in job["outcomes"]}
    assert by_ticket[good] == "Succeeded"
    assert by_ticket[bad] != "Succeeded"


def test_a_partial_ticket_still_gets_a_comparison(api, test_db):
    ticket_id = new_ticket(api, title="[mock-invalid] Odd")

    start(api, ticket_ids=[ticket_id], providers=["jev", "gpt"])

    assert test_db.comparisons.find_one({"ticket_id": ticket_id})["status"] != "Completed"


def test_all_eligible_means_open_or_in_progress(api):
    open_ticket, working = new_ticket(api), new_ticket(api)
    resolved, closed = new_ticket(api), new_ticket(api)
    api.patch(f"/api/tickets/{working}", json={"status": "In Progress"})
    api.patch(f"/api/tickets/{resolved}", json={"status": "Resolved"})
    api.patch(f"/api/tickets/{closed}", json={"status": "Closed"})

    job = start(api, all_eligible=True, providers=["jev"]).json()

    assert sorted(job["ticket_ids"]) == sorted([open_ticket, working])
    assert job["all_eligible"] is True


def test_all_eligible_never_repeats_a_side_that_already_succeeded(api, test_db):
    ticket_id = new_ticket(api)
    api.post(f"/api/tickets/{ticket_id}/runs/jev")

    job = start(api, all_eligible=True, providers=["jev", "gpt"]).json()

    assert (job["total"], job["completed"], job["skipped"]) == (2, 1, 1)
    assert test_db.ai_executions.count_documents({"provider": "jev"}) == 1
    skipped = next(o for o in job["outcomes"] if o["status"] == "Skipped")
    assert skipped["provider"] == "jev"
    assert skipped["execution_id"] is None


def test_an_earlier_success_on_a_different_model_does_not_cause_a_skip(api, test_db):
    ticket_id = new_ticket(api)
    api.post(f"/api/tickets/{ticket_id}/runs/jev")
    test_db.ai_executions.update_one({}, {"$set": {"requested_model": "another-model"}})

    job = start(api, all_eligible=True, providers=["jev"]).json()

    assert (job["completed"], job["skipped"]) == (1, 0)


def test_an_explicit_selection_runs_again_because_the_operator_asked(api, test_db):
    ticket_id = new_ticket(api)
    api.post(f"/api/tickets/{ticket_id}/runs/jev")

    start(api, ticket_ids=[ticket_id], providers=["jev"])

    assert test_db.ai_executions.count_documents({"provider": "jev"}) == 2


def test_a_ticket_deleted_before_its_turn_is_skipped(test_db, test_settings, api):
    ticket_id = new_ticket(api)
    job = bulk.create(test_db, bulk.BulkJobCreate(ticket_ids=[ticket_id], providers=["jev"]))
    api.delete(f"/api/tickets/{ticket_id}")

    bulk.run_job(test_db, job["job_id"], api.app.state.settings)

    saved = api.get(f"/api/bulk-jobs/{job['job_id']}").json()
    assert saved["status"] == "Completed"
    assert saved["skipped"] == 1
    assert test_db.ai_executions.count_documents({}) == 0


def test_invalid_requests_are_rejected_and_nothing_runs(api, test_db):
    ticket_id = new_ticket(api)

    assert start(api, ticket_ids=["SK-9999"], providers=["jev"]).status_code == 422
    assert (
        start(api, ticket_ids=[ticket_id], all_eligible=True, providers=["jev"]).status_code == 422
    )
    assert start(api, ticket_ids=[ticket_id], providers=[]).status_code == 422
    assert start(api, ticket_ids=[ticket_id], providers=["claude"]).status_code == 422
    assert test_db.ai_executions.count_documents({}) == 0
    assert test_db.bulk_jobs.count_documents({}) == 0


def test_no_eligible_tickets_is_a_clear_error(api):
    response = start(api, all_eligible=True, providers=["jev"])

    assert response.status_code == 422
    assert "eligible" in response.json()["detail"]


def test_repeated_values_in_a_request_run_once(api, test_db):
    ticket_id = new_ticket(api)

    job = start(api, ticket_ids=[ticket_id, ticket_id], providers=["jev", "jev"]).json()

    assert job["total"] == 1
    assert test_db.ai_executions.count_documents({}) == 1


def test_a_second_job_is_refused_while_one_is_active(api, test_db):
    ticket_id = new_ticket(api)
    test_db.bulk_jobs.insert_one({"job_id": "job_active", "status": "Running"})

    response = start(api, ticket_ids=[ticket_id], providers=["jev"])

    assert response.status_code == 409
    assert test_db.ai_executions.count_documents({}) == 0


def test_concurrency_stays_within_the_limit(test_db, test_settings, monkeypatch):
    settings = test_settings.model_copy(
        update={"mock_providers": True, "mock_delay_seconds": 0, "bulk_concurrency": 2}
    )
    lock, running, peak = threading.Lock(), [0], [0]
    real_run = bulk.run_provider

    def slow_run(*args, **kwargs):
        with lock:
            running[0] += 1
            peak[0] = max(peak[0], running[0])
        time.sleep(0.05)
        try:
            return real_run(*args, **kwargs)
        finally:
            with lock:
                running[0] -= 1

    monkeypatch.setattr(bulk, "run_provider", slow_run)
    with TestClient(create_app(settings)) as client:
        ids = [new_ticket(client) for _ in range(5)]
        job = start(client, ticket_ids=ids, providers=["jev"]).json()

    assert job["completed"] == 5
    assert peak[0] == 2


def test_restart_marks_unfinished_work_interrupted_and_does_not_rerun_it(test_settings, test_db):
    settings = test_settings.model_copy(update={"mock_providers": True, "mock_delay_seconds": 0})
    now = datetime.now(UTC)
    test_db.bulk_jobs.insert_many(
        [
            {"job_id": "job_running", "status": "Running", "created_at": now},
            {"job_id": "job_queued", "status": "Queued", "created_at": now},
            {"job_id": "job_done", "status": "Completed", "created_at": now},
        ]
    )
    test_db.ai_executions.insert_one({"execution_id": "exec_stuck", "status": "Running"})

    with TestClient(create_app(settings)):
        pass

    statuses = {j["job_id"]: j["status"] for j in test_db.bulk_jobs.find()}
    assert statuses["job_running"] == statuses["job_queued"] == BulkJobStatus.INTERRUPTED
    assert statuses["job_done"] == "Completed"
    interrupted = test_db.bulk_jobs.find_one({"job_id": "job_running"})
    assert interrupted["completed_at"] is not None
    assert "restart" in interrupted["error_summary"]
    stuck = test_db.ai_executions.find_one({"execution_id": "exec_stuck"})
    assert stuck["status"] == "Cancelled"
    assert "restart" in stuck["error"]["message"]
    assert test_db.ai_executions.count_documents({}) == 1


def test_jobs_are_listed_newest_first_and_unknown_is_404(api):
    ticket_id = new_ticket(api)
    first = start(api, ticket_ids=[ticket_id], providers=["jev"]).json()
    second = start(api, ticket_ids=[ticket_id], providers=["gpt"]).json()

    listed = api.get("/api/bulk-jobs?limit=1").json()

    assert listed["total"] == 2
    assert [j["job_id"] for j in listed["items"]] == [second["job_id"]]
    assert first["job_id"] != second["job_id"]
    assert api.get("/api/bulk-jobs/job_missing").status_code == 404
