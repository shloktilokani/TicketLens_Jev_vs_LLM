"""Bulk runs: many tickets, bounded concurrency, progress saved after every attempt.

Runs in-process (architecture.md, bulk processing). Unfinished work is marked Interrupted on the
next start and never resumed, so paid calls are not repeated without the operator asking.
"""

import logging
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

from pymongo.database import Database

from app.core.clock import utc_now
from app.core.settings import Settings
from app.core.taxonomy import BulkJobStatus, ExecutionStatus, Provider
from app.providers.registry import requested_model
from app.repositories import bulk_jobs, executions, tickets
from app.repositories.database import find_in
from app.schemas.bulk_jobs import BulkJobCreate
from app.services import app_settings, comparisons
from app.services.executions import run as run_provider

log = logging.getLogger("ticketlens")

SKIPPED = "Skipped"
RESTART_MESSAGE = "The backend restarted before this finished. It was not run again."


class BulkError(ValueError):
    def __init__(self, status_code: int, message: str):
        super().__init__(message)
        self.status_code = status_code


def select_tickets(db: Database, data: BulkJobCreate) -> list[str]:
    if data.all_eligible:
        ids = tickets.eligible_ids(db)
        if not ids:
            raise BulkError(422, "No eligible tickets: only Open or In Progress tickets qualify.")
        return ids
    known = {t["ticket_id"] for t in find_in(db, "tickets", "ticket_id", data.ticket_ids)}
    missing = [ticket_id for ticket_id in data.ticket_ids if ticket_id not in known]
    if missing:
        raise BulkError(422, f"Unknown tickets: {', '.join(missing[:5])}")
    return data.ticket_ids


def create(db: Database, data: BulkJobCreate) -> dict:
    # shortcut: check-then-insert can race, which is fine for one operator; add a partial unique
    # index if this ever has several users.
    if bulk_jobs.has_active(db):
        raise BulkError(409, "A bulk run is already in progress. Wait for it to finish.")
    ticket_ids = select_tickets(db, data)
    job = {
        "job_id": f"job_{uuid4().hex}",
        "ticket_ids": ticket_ids,
        "all_eligible": data.all_eligible,
        "providers": data.providers,
        "status": BulkJobStatus.QUEUED,
        "total": len(ticket_ids) * len(data.providers),
        "completed": 0,
        "failed": 0,
        "skipped": 0,
        "outcomes": [],
        "created_at": utc_now(),
        "started_at": None,
        "completed_at": None,
        "error_summary": None,
    }
    bulk_jobs.insert(db, job)
    return job


def already_succeeded(db: Database, job: dict, settings: Settings) -> dict[str, set[str]]:
    """Sides to skip per ticket. Only an all-eligible run skips: a selection is an explicit ask."""
    if not job["all_eligible"]:
        return {provider: set() for provider in job["providers"]}
    # Same model only: an old fake-AI success must not stop a real model from running.
    return {
        provider: executions.succeeded_ticket_ids(
            db, provider, requested_model(Provider(provider), settings), job["ticket_ids"]
        )
        for provider in job["providers"]
    }


def process_ticket(
    db: Database, job: dict, ticket_id: str, skip: dict[str, set[str]], settings: Settings
) -> None:
    """Every requested side of one ticket. A provider failure is recorded and never raised."""
    ticket = tickets.get(db, ticket_id)  # read now: it may have been edited or deleted since
    runs = {}
    for provider in job["providers"]:
        outcome = {"ticket_id": ticket_id, "provider": provider, "execution_id": None}
        if ticket is None or ticket_id in skip[provider]:
            bulk_jobs.record_outcome(db, job["job_id"], outcome | {"status": SKIPPED}, "skipped")
            continue
        execution = run_provider(db, ticket, provider, settings)
        runs[provider] = execution["execution_id"]
        ok = execution["status"] == ExecutionStatus.SUCCEEDED
        bulk_jobs.record_outcome(
            db,
            job["job_id"],
            outcome | {"status": execution["status"], "execution_id": runs[provider]},
            "completed" if ok else "failed",
        )
    if len(runs) == len(Provider):
        comparisons.create(db, ticket_id, runs[Provider.JEV], runs[Provider.GPT])


def finish(db: Database, job_id: str) -> None:
    job = bulk_jobs.get(db, job_id)
    failed = job["failed"]
    bulk_jobs.update(
        db,
        job_id,
        {
            "status": BulkJobStatus.COMPLETED_WITH_ERRORS if failed else BulkJobStatus.COMPLETED,
            "completed_at": utc_now(),
            "error_summary": f"{failed} of {job['total']} attempts failed." if failed else None,
        },
    )


def run_job(db: Database, job_id: str, settings: Settings) -> None:
    job = bulk_jobs.update(db, job_id, {"status": BulkJobStatus.RUNNING, "started_at": utc_now()})
    try:
        settings = app_settings.effective(db, settings)
        skip = already_succeeded(db, job, settings)
        with ThreadPoolExecutor(max_workers=settings.bulk_concurrency) as pool:
            futures = [
                pool.submit(process_ticket, db, job, ticket_id, skip, settings)
                for ticket_id in job["ticket_ids"]
            ]
        for future in futures:
            future.result()  # raises what a worker hit, such as the database going away
        finish(db, job_id)
    except Exception:
        log.exception("Bulk job %s stopped", job_id)
        bulk_jobs.update(
            db,
            job_id,
            {
                "status": BulkJobStatus.FAILED,
                "completed_at": utc_now(),
                "error_summary": "The bulk run stopped. Details are in the backend log.",
            },
        )


def mark_interrupted(db: Database) -> None:
    """On startup nothing can still be running, so whatever says it is was cut off."""
    # shortcut: assumes one backend process, which is the documented local setup; a multi-worker
    # deployment needs per-worker ownership of jobs.
    now = utc_now()
    bulk_jobs.mark_active_interrupted(db, {"completed_at": now, "error_summary": RESTART_MESSAGE})
    executions.cancel_running(db, now, RESTART_MESSAGE)
