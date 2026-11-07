import pytest

from app.core.redaction import REDACTED, redact
from app.providers.base import ProviderFailure, ProviderResult, build_input, failure_for_status
from app.providers.mock import MockProvider
from app.schemas.classification import NormalizedResult
from app.schemas.executions import Usage
from app.services.executions import run

TICKET = {
    "ticket_id": "SK-1001",
    "title": "Refund not received",
    "description": "I returned my headphones but the refund has not arrived.",
    "customer": {"name": "Aarav Mehta", "email": "aarav@example.test"},
    "order": {"order_id": "ORD-1", "product_name": "Headphones"},
    "submission_channel": "Website",
    "status": "Open",
    "final_classification": {"category": "Returns & Refunds", "subcategory": "Refund Delay"},
    "operator_notes": [{"text": "Customer called twice."}],
    "is_sample": True,
}


@pytest.fixture
def ticket(test_db):
    test_db.tickets.insert_one(dict(TICKET))
    return TICKET


# --- canonical input -----------------------------------------------------------------------


def test_input_holds_only_ticket_content_and_taxonomy():
    data = build_input(TICKET).model_dump()

    assert data["title"] == TICKET["title"]
    assert data["description"] == TICKET["description"]
    assert data["taxonomy_version"] == "1.0"
    assert len(data["categories"]) == 6
    text = str(data)
    for forbidden in (
        "final_classification",
        "Customer called twice",
        "aarav@example.test",
        "is_sample",
    ):
        assert forbidden not in text


# --- errors and redaction ------------------------------------------------------------------


@pytest.mark.parametrize(
    ("status", "kind", "retryable"),
    [
        (400, "invalid_request", False),
        (422, "invalid_request", False),
        (401, "auth", False),
        (403, "auth", False),
        (402, "insufficient_credits", False),
        (429, "rate_limited", True),
        (500, "server_error", True),
        (503, "server_error", True),
    ],
)
def test_http_status_maps_to_a_safe_failure(status, kind, retryable):
    failure = failure_for_status("Jev", status)

    assert (failure.kind, failure.retryable, failure.http_status) == (kind, retryable, status)
    assert "Jev" in failure.message


def test_redaction_removes_credentials_at_any_depth():
    payload = {
        "headers": {"Authorization": "Bearer sk-real", "Accept": "json"},
        "body": {"api_key": "sk-real", "items": [{"token": "t"}, {"text": "keep me"}]},
    }

    cleaned = redact(payload)

    assert cleaned["headers"] == {"Authorization": REDACTED, "Accept": "json"}
    assert cleaned["body"]["api_key"] == REDACTED
    assert cleaned["body"]["items"] == [{"token": REDACTED}, {"text": "keep me"}]
    assert "sk-real" not in str(cleaned)
    assert payload["body"]["api_key"] == "sk-real"  # the original is not modified


# --- mock providers ------------------------------------------------------------------------


@pytest.mark.parametrize("provider", ["jev", "gpt"])
def test_mock_output_follows_the_normalized_schema(provider):
    result = MockProvider(provider).classify(build_input(TICKET))

    normalized = NormalizedResult(**result.output)
    assert (normalized.category, normalized.subcategory) == ("Returns & Refunds", "Refund Delay")
    assert result.requested_model == f"mock-{provider}"
    assert result.usage.usage_source == "unavailable"  # mocks never invent token counts


def test_mock_jev_marks_free_text_unsupported_and_gpt_writes_it():
    jev = NormalizedResult(**MockProvider("jev").classify(build_input(TICKET)).output)
    gpt = NormalizedResult(**MockProvider("gpt").classify(build_input(TICKET)).output)

    assert jev.summary is None and jev.unsupported_fields == ["summary", "suggested_resolution"]
    assert gpt.summary and gpt.suggested_resolution and gpt.unsupported_fields == []


def test_mock_is_deterministic():
    first = MockProvider("gpt").classify(build_input(TICKET)).output
    assert MockProvider("gpt").classify(build_input(TICKET)).output == first


@pytest.mark.parametrize(
    ("marker", "kind"), [("[mock-fail]", "server_error"), ("[mock-timeout]", "timeout")]
)
def test_mock_failures_can_be_triggered_from_the_title(marker, kind):
    ticket = TICKET | {"title": f"Broken {marker}"}

    with pytest.raises(ProviderFailure) as raised:
        MockProvider("jev").classify(build_input(ticket))

    assert raised.value.kind == kind


# --- execution recording -------------------------------------------------------------------


def mock_settings(test_settings):
    return test_settings.model_copy(update={"mock_providers": True, "mock_delay_seconds": 0})


def test_successful_run_is_recorded(test_db, test_settings, ticket):
    record = run(test_db, ticket, "jev", mock_settings(test_settings))

    assert record["status"] == "Succeeded"
    assert record["provider"] == "jev"
    assert record["requested_model"] == "mock-jev"
    assert record["normalized_result"]["subcategory"] == "Refund Delay"
    assert record["duration_ms"] >= 0
    assert record["completed_at"] >= record["started_at"]
    assert record["input_snapshot"]["title"] == TICKET["title"]
    assert record["error"] is None
    assert test_db.ai_executions.count_documents({"execution_id": record["execution_id"]}) == 1


def test_record_exists_before_the_provider_answers(test_db, test_settings, ticket, monkeypatch):
    seen = {}

    def classify(self, data):
        seen["status"] = test_db.ai_executions.find_one({"ticket_id": "SK-1001"})["status"]
        return original(self, data)

    original = MockProvider.classify
    monkeypatch.setattr(MockProvider, "classify", classify)
    run(test_db, ticket, "gpt", mock_settings(test_settings))

    assert seen["status"] == "Running"


@pytest.mark.parametrize(
    ("marker", "status", "kind"),
    [
        ("[mock-fail]", "Failed", "server_error"),
        ("[mock-timeout]", "Timed Out", "timeout"),
        ("[mock-invalid]", "Invalid Response", "invalid_response"),
    ],
)
def test_failed_runs_are_still_recorded(test_db, test_settings, ticket, marker, status, kind):
    record = run(
        test_db, ticket | {"title": f"Broken {marker}"}, "jev", mock_settings(test_settings)
    )

    assert record["status"] == status
    assert record["error"]["code"] == kind
    assert record["normalized_result"] is None
    assert record["completed_at"] is not None


def test_missing_key_is_recorded_as_not_configured(test_db, test_settings, ticket):
    openai = test_settings.model_copy(update={"llm_backend": "openai"})
    record = run(test_db, ticket, "gpt", openai)  # live mode, no OpenAI key

    assert record["status"] == "Failed"
    assert record["error"]["code"] == "not_configured"
    assert "OPENAI_API_KEY" in record["error"]["message"]


def test_unexpected_crash_is_recorded_not_raised(test_db, test_settings, ticket, monkeypatch):
    monkeypatch.setattr(MockProvider, "classify", lambda self, data: 1 / 0)

    record = run(test_db, ticket, "jev", mock_settings(test_settings))

    assert record["status"] == "Failed"
    assert record["error"]["code"] == "unexpected"
    assert "ZeroDivision" not in record["error"]["message"]


def test_payloads_are_redacted_before_saving(test_db, test_settings, ticket, monkeypatch):
    def leaky(self, data):
        return ProviderResult(
            requested_model="mock-jev",
            actual_model="mock-jev",
            request_payload={"headers": {"Authorization": "Bearer sk-live-secret"}},
            response_payload={"ok": True},
            output=original(self, data).output,
            usage=Usage(),
        )

    original = MockProvider.classify
    monkeypatch.setattr(MockProvider, "classify", leaky)

    record = run(test_db, ticket, "jev", mock_settings(test_settings))

    assert "sk-live-secret" not in str(
        test_db.ai_executions.find_one({"execution_id": record["execution_id"]})
    )
