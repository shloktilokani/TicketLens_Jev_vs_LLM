from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.core.taxonomy import TAXONOMY_VERSION
from app.schemas.bulk_jobs import BulkJobCreate
from app.schemas.classification import Classification, FinalClassification, NormalizedResult
from app.schemas.executions import Execution
from app.schemas.tickets import TicketCreate

VALID = {
    "category": "Returns & Refunds",
    "subcategory": "Refund Delay",
    "priority": "Medium",
    "sentiment": "Negative",
    "escalation_required": False,
}

TICKET = {
    "title": "Refund not received",
    "description": "I returned my headphones last week but the refund has not arrived.",
    "customer_name": "Aarav Mehta",
    "customer_email": "aarav@example.test",
    "submission_channel": "Website",
}


def test_valid_classification_is_accepted():
    assert Classification(**VALID).subcategory == "Refund Delay"


@pytest.mark.parametrize(
    "change",
    [
        {"subcategory": "Password Reset"},  # belongs to Account & Login
        {"category": "Unknown"},
        {"priority": "Urgent"},
        {"sentiment": "Angry"},
    ],
)
def test_invalid_classification_is_rejected(change):
    with pytest.raises(ValidationError):
        Classification(**(VALID | change))


def test_final_classification_records_taxonomy_version():
    assert FinalClassification(**VALID).taxonomy_version == TAXONOMY_VERSION


def test_jev_result_can_mark_free_text_unsupported():
    result = NormalizedResult(
        **VALID, confidence={"category": 0.91}, unsupported_fields=["summary"]
    )

    assert result.summary is None
    assert result.unsupported_fields == ["summary"]


def test_execution_records_taxonomy_version():
    execution = Execution(
        execution_id="exec_1",
        ticket_id="SK-1001",
        provider="jev",
        requested_model="jev-latest",
        status="Running",
        started_at=datetime.now(UTC),
        input_snapshot={},
        prompt_version="1.0",
    )

    assert execution.taxonomy_version == TAXONOMY_VERSION


def test_ticket_create_trims_short_fields_and_keeps_description_exactly():
    description = "  Line one.\n\nLine two, exactly as typed.  "

    ticket = TicketCreate(
        **(
            TICKET
            | {
                "title": "  Refund  ",
                "customer_email": " Aarav@Example.TEST ",
                "description": description,
            }
        )
    )

    assert ticket.title == "Refund"
    assert ticket.customer_email == "aarav@example.test"
    assert ticket.description == description


@pytest.mark.parametrize(
    "change",
    [
        {"title": "   "},
        {"description": " \n "},
        {"customer_email": "not-an-email"},
        {"submission_channel": "Fax"},
        {"title": "x" * 201},
    ],
)
def test_invalid_ticket_input_is_rejected(change):
    with pytest.raises(ValidationError):
        TicketCreate(**(TICKET | change))


def test_ticket_create_rejects_missing_required_field():
    with pytest.raises(ValidationError):
        TicketCreate(**{k: v for k, v in TICKET.items() if k != "customer_name"})


@pytest.mark.parametrize(
    ("selection", "ok"),
    [
        ({"ticket_ids": ["SK-1001"]}, True),
        ({"all_eligible": True}, True),
        ({}, False),
        ({"ticket_ids": ["SK-1001"], "all_eligible": True}, False),
        ({"ticket_ids": []}, False),
    ],
)
def test_bulk_job_needs_exactly_one_selection(selection, ok):
    request = {"providers": ["jev", "gpt"]} | selection
    if ok:
        BulkJobCreate(**request)
    else:
        with pytest.raises(ValidationError):
            BulkJobCreate(**request)


def test_bulk_job_needs_a_provider():
    with pytest.raises(ValidationError):
        BulkJobCreate(ticket_ids=["SK-1001"], providers=[])
