from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.core.pricing import estimate, snapshot_for
from app.core.taxonomy import Provider
from app.main import create_app
from app.providers.base import ProviderResult
from app.providers.mock import MockProvider
from app.schemas.executions import PricingSnapshot, Usage

NEW = {
    "title": "Refund not received",
    "description": "I returned my headphones but the refund has not arrived.",
    "customer_name": "Aarav Mehta",
    "customer_email": "aarav@example.test",
    "submission_channel": "Website",
}
RATES = PricingSnapshot(
    input_per_million=Decimal("0.042"), output_per_million=Decimal("2"), pricing_version="test-1"
)


# --- cost formula ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("tokens_in", "tokens_out", "expected"),
    [
        (1_000_000, 0, Decimal("0.042")),
        (120, 12, Decimal("0.00002904")),  # exact: no floating-point rounding
        (0, 0, Decimal("0")),
    ],
)
def test_cost_formula(tokens_in, tokens_out, expected):
    usage = Usage(
        input_tokens=tokens_in, output_tokens=tokens_out, usage_source="provider_reported"
    )

    cost = estimate(usage, RATES)

    assert cost.amount == expected
    assert (cost.currency, cost.is_estimate) == ("USD", True)


@pytest.mark.parametrize(
    "usage",
    [
        Usage(),
        Usage(input_tokens=10, usage_source="provider_reported"),
        Usage(output_tokens=10, usage_source="provider_reported"),
    ],
)
def test_missing_usage_gives_no_cost(usage):
    assert estimate(usage, RATES) is None


def test_no_rates_gives_no_cost():
    usage = Usage(input_tokens=1, output_tokens=1, usage_source="provider_reported")

    assert estimate(usage, None) is None


# --- which rates apply -----------------------------------------------------------------------


def test_local_models_cost_nothing(test_settings):
    local = test_settings.model_copy(update={"jev_base_url": "http://127.0.0.1:11434"})

    for provider in Provider:
        rates = snapshot_for(provider, local)
        assert rates.input_per_million == 0 and rates.output_per_million == 0
        assert rates.pricing_version == "local-no-charge"


def test_hosted_jev_uses_the_published_rate(test_settings):
    rates = snapshot_for(Provider.JEV, test_settings)  # default base URL is TypeSafe's hosted API

    assert rates.input_per_million == Decimal("0.042")
    assert rates.output_per_million == 0
    assert rates.pricing_version == "typesafe-jev-2026-11"


def test_openai_and_fake_providers_are_not_priced(test_settings):
    openai = test_settings.model_copy(update={"llm_backend": "openai"})
    fake = test_settings.model_copy(update={"mock_providers": True})

    assert snapshot_for(Provider.GPT, openai) is None
    assert snapshot_for(Provider.JEV, fake) is None


# --- API -------------------------------------------------------------------------------------


@pytest.fixture
def api(test_settings, test_db):
    settings = test_settings.model_copy(update={"mock_providers": True, "mock_delay_seconds": 0})
    with TestClient(create_app(settings)) as client:
        yield client


def ticket(api, **changes) -> str:
    return api.post("/api/tickets", json=NEW | changes).json()["ticket_id"]


def run(api, ticket_id: str, provider: str) -> dict:
    return api.post(f"/api/tickets/{ticket_id}/runs/{provider}").json()


@pytest.fixture
def priced(test_settings, test_db, monkeypatch):
    """A local (zero-rate) app whose adapter reports real token counts, with no network."""
    settings = test_settings.model_copy(update={"jev_base_url": "http://127.0.0.1:11434"})

    def classify(self, data):
        output = MockProvider("jev").classify(data).output
        return ProviderResult(
            requested_model="autotrust-jev:9b",
            actual_model="autotrust-jev:9b",
            request_payload={
                "headers": {"Authorization": "Bearer sk-secret"},
                "body": {"state": "x"},
            },
            response_payload={"ok": True},
            output=output,
            usage=Usage(
                input_tokens=1000,
                output_tokens=0,
                total_tokens=1000,
                usage_source="provider_reported",
            ),
        )

    monkeypatch.setattr("app.providers.jev.JevAdapter.classify", classify)
    with TestClient(create_app(settings)) as client:
        yield client


def test_run_stores_rates_and_cost_as_exact_decimals(priced, test_db):
    execution = run(priced, ticket(priced), "jev")

    assert execution["pricing_snapshot"]["pricing_version"] == "local-no-charge"
    assert Decimal(execution["estimated_cost"]["amount"]) == 0
    stored = test_db.ai_executions.find_one({"execution_id": execution["execution_id"]})
    assert type(stored["estimated_cost"]["amount"]).__name__ == "Decimal128"


def test_old_runs_keep_their_rates_when_rates_change(priced, test_db, monkeypatch):
    first = run(priced, ticket(priced), "jev")["execution_id"]

    monkeypatch.setattr("app.core.pricing.LOCAL_VERSION", "local-new-rates")
    second = run(priced, ticket(priced), "jev")["execution_id"]

    assert (
        priced.get(f"/api/executions/{first}").json()["pricing_snapshot"]["pricing_version"]
        == "local-no-charge"
    )
    assert (
        priced.get(f"/api/executions/{second}").json()["pricing_snapshot"]["pricing_version"]
        == "local-new-rates"
    )


def test_stored_records_hold_no_secrets(priced, test_db):
    execution = run(priced, ticket(priced), "jev")

    body = priced.get(f"/api/executions/{execution['execution_id']}").text

    assert "sk-secret" not in body
    assert "sk-secret" not in str(test_db.ai_executions.find_one({}))
    assert "[REDACTED]" in body


def test_list_filters_by_provider_status_ticket_and_date(api, test_db):
    first, second = ticket(api), ticket(api, title="Broken [mock-fail]")
    run(api, first, "jev")
    run(api, first, "gpt")
    run(api, second, "jev")

    def ids(**params):
        return api.get("/api/executions", params=params).json()

    assert ids()["total"] == 3
    assert ids(provider="gpt")["total"] == 1
    assert ids(status="Failed")["total"] == 1
    assert ids(ticket_id=second)["items"][0]["status"] == "Failed"
    tomorrow = (datetime.now(UTC) + timedelta(days=1)).date().isoformat()
    assert ids(date_from=tomorrow)["total"] == 0
    assert ids(date_to=tomorrow)["total"] == 3
    assert api.get("/api/executions", params={"provider": "claude"}).status_code == 422
    assert api.get("/api/executions", params={"status": "Nope"}).status_code == 422
    assert api.get("/api/executions", params={"page_size": 101}).status_code == 422


def test_list_is_newest_first_paged_and_leaves_out_payloads(api):
    first = ticket(api)
    for provider in ("jev", "gpt", "jev"):
        last = run(api, first, provider)

    page = api.get("/api/executions", params={"page_size": 2}).json()

    assert page["items"][0]["execution_id"] == last["execution_id"]
    assert (len(page["items"]), page["total"], page["page"]) == (2, 3, 1)
    assert "request_payload_redacted" not in page["items"][0]
    assert "input_snapshot" not in page["items"][0]


def test_detail_includes_payloads_and_failed_runs_stay_inspectable(api):
    failed = run(api, ticket(api, title="Broken [mock-fail]"), "jev")

    detail = api.get(f"/api/executions/{failed['execution_id']}").json()

    assert detail["status"] == "Failed"
    assert detail["error"]["code"] == "server_error"
    assert detail["input_snapshot"]["title"] == "Broken [mock-fail]"
    assert api.get("/api/executions/exec_missing").status_code == 404
