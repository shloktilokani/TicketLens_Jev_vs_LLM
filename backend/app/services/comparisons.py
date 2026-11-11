"""Compare one Jev run with one LLM run (key "gpt") on the five shared fields.

Agreement is not accuracy, and no winner is ever chosen: the operator picks the final answer.
"""

from uuid import uuid4

from pymongo.database import Database

from app.core.clock import utc_now
from app.core.taxonomy import ComparisonStatus, ExecutionStatus, Provider
from app.repositories import comparisons, executions

SHARED_FIELDS = ["category", "subcategory", "priority", "sentiment", "escalation_required"]


class ComparisonError(ValueError):
    def __init__(self, status_code: int, message: str):
        super().__init__(message)
        self.status_code = status_code


def field_comparison(jev: dict | None, gpt: dict | None) -> dict:
    """Per-field values; `match` is None unless both sides have a validated result."""
    both = jev is not None and gpt is not None
    return {
        field: {
            "jev": jev[field] if jev else None,
            "gpt": gpt[field] if gpt else None,
            "match": jev[field] == gpt[field] if both else None,
        }
        for field in SHARED_FIELDS
    }


def status_of(jev: dict | None, gpt: dict | None) -> ComparisonStatus:
    if jev and gpt:
        return ComparisonStatus.COMPLETED
    if jev or gpt:
        return ComparisonStatus.PARTIAL  # the successful result is kept and shown
    return ComparisonStatus.UNAVAILABLE


def load(db: Database, execution_id: str, ticket_id: str, provider: Provider) -> dict:
    execution = executions.get(db, execution_id)
    if execution is None:
        raise ComparisonError(404, f"Execution {execution_id} not found")
    if execution["ticket_id"] != ticket_id or execution["provider"] != provider:
        raise ComparisonError(
            422, f"Execution {execution_id} is not a {provider.value} run of {ticket_id}"
        )
    if execution["status"] == ExecutionStatus.RUNNING:
        raise ComparisonError(409, f"Execution {execution_id} is still running")
    return execution


def create(db: Database, ticket_id: str, jev_execution_id: str, gpt_execution_id: str) -> dict:
    jev = load(db, jev_execution_id, ticket_id, Provider.JEV)["normalized_result"]
    gpt = load(db, gpt_execution_id, ticket_id, Provider.GPT)["normalized_result"]
    fields = field_comparison(jev, gpt)
    comparable = len(SHARED_FIELDS) if jev and gpt else 0
    agreed = sum(1 for f in fields.values() if f["match"])
    doc = {
        "comparison_id": f"cmp_{uuid4().hex}",
        "ticket_id": ticket_id,
        "jev_execution_id": jev_execution_id,
        "gpt_execution_id": gpt_execution_id,
        "status": status_of(jev, gpt),
        "field_comparison": fields,
        "agreement_count": agreed,
        "comparable_field_count": comparable,
        "agreement_rate": agreed / comparable if comparable else None,
        "created_at": utc_now(),
    }
    comparisons.insert(db, doc)
    executions.link_comparison(db, [jev_execution_id, gpt_execution_id], doc["comparison_id"])
    return doc
