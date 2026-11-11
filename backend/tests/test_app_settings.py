from decimal import Decimal

import httpx
import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.core import taxonomy
from app.core.settings import Settings
from app.core.taxonomy import Provider
from app.jobs import bulk
from app.main import create_app
from app.providers import jev, ollama
from app.providers.base import build_input
from app.services import app_settings

NEW = {
    "title": "Refund not received",
    "description": "I returned my headphones but the refund has not arrived.",
    "customer_name": "Aarav Mehta",
    "customer_email": "aarav@example.test",
    "submission_channel": "Website",
}
FINAL = {
    "category": "Returns & Refunds",
    "subcategory": "Refund Delay",
    "priority": "Medium",
    "sentiment": "Negative",
    "escalation_required": False,
}


@pytest.fixture
def api(test_settings, test_db):
    settings = test_settings.model_copy(update={"mock_providers": True, "mock_delay_seconds": 0})
    with TestClient(create_app(settings)) as client:
        yield client


@pytest.fixture
def local(test_settings) -> Settings:
    return test_settings.model_copy(
        update={"jev_base_url": "http://127.0.0.1:11434", "jev_model": "autotrust-jev:9b"}
    )


def categories(**changes) -> dict:
    return {name: list(subs) for name, subs in taxonomy.as_dict()["categories"].items()} | changes


def new_ticket(api) -> str:
    return api.post("/api/tickets", json=NEW).json()["ticket_id"]


# --- reading -----------------------------------------------------------------------------


def test_defaults_show_with_no_saved_settings(api):
    view = api.get("/api/settings").json()

    assert view["jev_model"] == "mock-jev"
    assert view["llm_model"] == "mock-gpt"
    assert view["jev_escalation_threshold"] == 0.5
    assert view["bulk_concurrency"] == 2
    assert view["prompt"]["version"] == "1.0"
    assert "ShopKart" in view["prompt"]["instructions"]
    assert view["taxonomy"]["version"] == "1.0"
    assert len(view["taxonomy"]["categories"]) == 6
    assert view["pricing"] == []
    assert view["providers"]["jev"]["configured"] is True


def test_api_keys_can_never_be_read(test_settings, test_db):
    keyed = test_settings.model_copy(
        update={
            "typesafe_api_key": SecretStr("ts-secret-value"),
            "openai_api_key": SecretStr("oa-secret-value"),
        }
    )
    with TestClient(create_app(keyed)) as client:
        text = client.get("/api/settings").text

    assert "secret-value" not in text


@pytest.mark.parametrize(
    "field", ["typesafe_api_key", "openai_api_key", "mongodb_uri", "jev_base_url", "api_key"]
)
def test_keys_and_connection_details_cannot_be_changed(api, test_db, field):
    response = api.patch("/api/settings", json={field: "http://attacker.example"})

    assert response.status_code == 422
    assert test_db.app_settings.count_documents({}) == 0


# --- plain values -------------------------------------------------------------------------


def test_threshold_and_concurrency_persist_and_take_effect(test_settings, test_db):
    settings = test_settings.model_copy(update={"mock_providers": True})
    with TestClient(create_app(settings)) as client:
        response = client.patch(
            "/api/settings", json={"jev_escalation_threshold": 0.7, "bulk_concurrency": 4}
        )
        assert response.status_code == 200, response.text

    # A fresh start reads them back from MongoDB.
    with TestClient(create_app(settings)) as client:
        view = client.get("/api/settings").json()
    assert (view["jev_escalation_threshold"], view["bulk_concurrency"]) == (0.7, 4)
    active = app_settings.effective(test_db, settings)
    assert (active.jev_escalation_threshold, active.bulk_concurrency) == (0.7, 4)


@pytest.mark.parametrize(
    "body",
    [
        {"jev_escalation_threshold": 1.5},
        {"jev_escalation_threshold": -0.1},
        {"bulk_concurrency": 0},
        {"bulk_concurrency": 11},
        {},
    ],
)
def test_out_of_range_values_are_rejected(api, test_db, body):
    assert api.patch("/api/settings", json=body).status_code == 422
    assert test_db.app_settings.count_documents({}) == 0


def test_a_bulk_run_uses_the_saved_concurrency(api, test_db, monkeypatch):
    seen = []
    real_pool = bulk.ThreadPoolExecutor

    def pool(max_workers):
        seen.append(max_workers)
        return real_pool(max_workers=max_workers)

    monkeypatch.setattr(bulk, "ThreadPoolExecutor", pool)
    api.patch("/api/settings", json={"bulk_concurrency": 3})

    api.post("/api/bulk-jobs", json={"ticket_ids": [new_ticket(api)], "providers": ["jev"]})

    assert seen == [3]


# --- models -------------------------------------------------------------------------------


def test_saved_models_reach_the_right_side(local, test_db, monkeypatch):
    monkeypatch.setattr(app_settings, "available_models", lambda *_: ["qwen3:14b", "jev-2"])
    with TestClient(create_app(local)) as client:
        response = client.patch(
            "/api/settings", json={"jev_model": "jev-2", "llm_model": "qwen3:14b"}
        )
        assert response.status_code == 200, response.text
        status = client.get("/api/providers/status").json()

    active = app_settings.effective(test_db, local)
    assert (active.jev_model, active.ollama_model) == ("jev-2", "qwen3:14b")
    assert "qwen3:14b" in status["gpt"]["label"]


@pytest.mark.parametrize("bad", ["", "a b", "x" * 200, "model;rm -rf", "../etc/passwd"])
def test_a_badly_formed_model_name_is_rejected(api, bad):
    assert api.patch("/api/settings", json={"llm_model": bad}).status_code == 422


def test_a_model_the_server_does_not_have_is_rejected(local, test_db, monkeypatch):
    monkeypatch.setattr(app_settings, "available_models", lambda *_: ["qwen3:8b"])
    with TestClient(create_app(local)) as client:
        response = client.patch("/api/settings", json={"llm_model": "made-up:1b"})

    assert response.status_code == 422
    assert "qwen3:8b" in response.json()["detail"]


def test_the_documented_jev_alias_is_always_allowed(local, test_db, monkeypatch):
    monkeypatch.setattr(app_settings, "available_models", lambda *_: ["jev-2"])
    with TestClient(create_app(local)) as client:
        assert client.patch("/api/settings", json={"jev_model": "jev-latest"}).status_code == 200


def test_a_model_can_be_saved_when_the_server_is_unreachable(local, test_db, monkeypatch):
    def down(*_):
        raise app_settings.ProviderFailure("network", "Could not reach it.")

    monkeypatch.setattr(app_settings, "available_models", down)
    with TestClient(create_app(local)) as client:
        assert client.patch("/api/settings", json={"llm_model": "qwen3:14b"}).status_code == 200


def test_model_list_parses_the_servers_answer_and_sends_the_key_only_to_it(local):
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"], seen["auth"] = str(request.url), request.headers.get("authorization")
        return httpx.Response(200, json={"data": [{"id": "jev-b"}, {"id": "jev-a"}]})

    keyed = local.model_copy(
        update={"jev_base_url": "https://api.typesafe.ai", "typesafe_api_key": SecretStr("k-1")}
    )
    client = httpx.Client(transport=httpx.MockTransport(handler))

    assert app_settings.available_models(keyed, "jev", client) == ["jev-a", "jev-b"]
    assert seen == {"url": "https://api.typesafe.ai/v1/models", "auth": "Bearer k-1"}


def test_models_endpoint_reports_a_safe_error(local, test_db, monkeypatch):
    def down(*_):
        raise app_settings.ProviderFailure("network", "Could not reach it. Is it running?")

    monkeypatch.setattr(app_settings, "available_models", down)
    with TestClient(create_app(local)) as client:
        body = client.get("/api/settings/models/llm").json()

    assert body == {"models": [], "error": "Could not reach it. Is it running?"}


# --- prompts ------------------------------------------------------------------------------


def test_a_new_prompt_gets_a_version_and_old_runs_keep_theirs(api, test_db):
    ticket_id = new_ticket(api)
    first = api.post(f"/api/tickets/{ticket_id}/runs/gpt").json()
    assert first["prompt_version"] == "1.0"

    response = api.put("/api/settings/prompt", json={"instructions": "Classify ShopKart tickets."})
    assert response.status_code == 200, response.text
    assert response.json()["prompt"]["version"] == "1.1"

    second = api.post(f"/api/tickets/{ticket_id}/runs/gpt").json()
    assert second["prompt_version"] == "1.1"
    assert second["input_snapshot"]["instructions"] == "Classify ShopKart tickets."
    old = api.get(f"/api/executions/{first['execution_id']}").json()
    assert old["prompt_version"] == "1.0"
    assert "ShopKart, an Indian" in old["input_snapshot"]["instructions"]

    history = api.get("/api/settings").json()["prompt"]["history"]
    assert [h["version"] for h in history] == ["1.1", "1.0"]


def test_both_sides_receive_the_same_saved_prompt():
    data = build_input(
        {
            "ticket_id": "SK-1",
            "title": "t",
            "description": "d",
            "order": {"order_id": None, "product_name": None},
            "submission_channel": "Email",
        },
        instructions="Saved prompt text.",
    )

    assert "Saved prompt text." in ollama.build_request("m", data)["messages"][0]["content"]
    questions = jev.build_request("m", data)["questions"]
    assert "Saved prompt text." in questions["category"]["instructions"]


@pytest.mark.parametrize("text", ["", "   ", "x" * 5001])
def test_a_blank_or_huge_prompt_is_rejected(api, text):
    assert api.put("/api/settings/prompt", json={"instructions": text}).status_code == 422
    assert api.get("/api/settings").json()["prompt"]["version"] == "1.0"


# --- taxonomy -----------------------------------------------------------------------------


def test_adding_labels_bumps_the_version_and_reaches_everything(api, test_db):
    body = categories(
        **{
            "Orders & Delivery": [*taxonomy.SUBCATEGORIES["Orders & Delivery"], "Gift Orders"],
            "Loyalty": ["Points Balance", "Points Expiry"],
        }
    )

    response = api.put("/api/settings/taxonomy", json={"categories": body})

    assert response.status_code == 200, response.text
    assert response.json()["taxonomy"]["version"] == "1.1"
    public = api.get("/api/taxonomy").json()
    assert public["version"] == "1.1"
    assert "Loyalty" in public["categories"]
    assert taxonomy.is_valid_pair("Loyalty", "Points Expiry")

    ticket_id = new_ticket(api)
    assert api.get(f"/api/tickets/{ticket_id}").json()["taxonomy_version"] == "1.1"
    response = api.put(
        f"/api/tickets/{ticket_id}/final-classification",
        json=FINAL | {"category": "Loyalty", "subcategory": "Points Balance"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["final_classification"]["taxonomy_version"] == "1.1"
    assert '"Loyalty"' in str(ollama.system_prompt()).replace("'", '"')
    data = build_input(test_db.tickets.find_one({"ticket_id": ticket_id}, {"_id": 0}))
    assert "Loyalty" in jev.build_request("m", data)["questions"]["category"]["criteria"]
    assert "Loyalty" in ollama.build_request("m", data)["format"]["properties"]["category"]["enum"]


def test_saved_taxonomy_survives_a_restart(test_settings, test_db):
    with TestClient(create_app(test_settings)) as client:
        body = categories(Loyalty=["Points Balance", "Points Expiry"])
        assert client.put("/api/settings/taxonomy", json={"categories": body}).status_code == 200
    taxonomy.reset()

    with TestClient(create_app(test_settings)) as client:
        assert "Loyalty" in client.get("/api/taxonomy").json()["categories"]


def test_unused_labels_can_be_removed(api):
    body = categories()
    body["General Enquiries"].remove("Feedback")

    assert api.put("/api/settings/taxonomy", json={"categories": body}).status_code == 200
    assert not taxonomy.is_valid_pair("General Enquiries", "Feedback")


@pytest.mark.parametrize(
    "use",
    ["final", "run", "label"],
)
def test_a_label_in_use_cannot_be_removed_or_renamed(api, test_db, use):
    ticket_id = new_ticket(api)
    answer = FINAL
    if use == "final":
        api.put(f"/api/tickets/{ticket_id}/final-classification", json=answer)
    elif use == "run":
        test_db.ai_executions.insert_one({"ticket_id": ticket_id, "normalized_result": answer})
    else:
        test_db.evaluation_labels.insert_one({"ticket_id": ticket_id, "expected": answer})
    body = categories()
    body["Returns & Refunds"].remove("Refund Delay")
    body["Returns & Refunds"].append("Refund Late")

    response = api.put("/api/settings/taxonomy", json={"categories": body})

    assert response.status_code == 409
    assert "Refund Delay" in response.json()["detail"]
    assert api.get("/api/taxonomy").json()["version"] == "1.0"


@pytest.mark.parametrize(
    "change",
    [
        {"Empty": []},
        {"One": ["Only one"]},
        {"Too many": [f"Option {i}" for i in range(17)]},
        {"Blank": ["  ", "Fine"]},
        {"Repeats": ["Same", "Same"]},
        {"Taken": ["Refund Delay", "Something Else"]},
        {"Long": ["x" * 81, "Fine"]},
    ],
)
def test_invalid_taxonomies_are_rejected(api, change):
    response = api.put("/api/settings/taxonomy", json={"categories": categories(**change)})

    assert response.status_code == 422
    assert api.get("/api/taxonomy").json()["version"] == "1.0"


def test_jev_limit_of_sixteen_categories_is_enforced(api):
    extra = {f"Category {i}": [f"A{i}", f"B{i}"] for i in range(11)}

    response = api.put("/api/settings/taxonomy", json={"categories": categories(**extra)})

    assert response.status_code == 422


# --- pricing ------------------------------------------------------------------------------


def entry(**changes) -> dict:
    return {
        "provider": "gpt",
        "model": "qwen3:8b",
        "input_per_million": "1.50",
        "output_per_million": "2.00",
    } | changes


def test_saved_rates_are_used_and_old_runs_keep_theirs(local, test_db):
    with TestClient(create_app(local)) as client:
        db = client.app.state.db  # the app's own connection, which reads money as exact decimals
        before = app_settings.rates_for(db, Provider.GPT, local)
        assert before.input_per_million == 0
        response = client.put("/api/settings/pricing", json={"entries": [entry()]})
        assert response.status_code == 200, response.text
        assert Decimal(response.json()["pricing"][0]["input_per_million"]) == Decimal("1.50")

        rates = app_settings.rates_for(db, Provider.GPT, local)
        assert rates.input_per_million == Decimal("1.50")
        assert rates.output_per_million == Decimal("2.00")
        assert rates.pricing_version.startswith("settings-")
        # A model with no entry keeps the built-in behaviour.
        assert app_settings.rates_for(db, Provider.JEV, local).pricing_version == "local-no-charge"


def test_fake_runs_are_never_priced_even_with_saved_rates(test_settings, test_db):
    fake = test_settings.model_copy(update={"mock_providers": True})
    with TestClient(create_app(fake)) as client:
        client.put("/api/settings/pricing", json={"entries": [entry(model="mock-gpt")]})

    assert app_settings.rates_for(test_db, Provider.GPT, fake) is None


@pytest.mark.parametrize(
    "bad",
    [
        entry(input_per_million="-1"),
        entry(output_per_million="abc"),
        entry(provider="claude"),
        entry(model="bad model"),
    ],
)
def test_invalid_rates_are_rejected(api, test_db, bad):
    assert api.put("/api/settings/pricing", json={"entries": [bad]}).status_code == 422
    assert test_db.app_settings.count_documents({}) == 0


def test_the_same_model_cannot_be_priced_twice(api):
    response = api.put("/api/settings/pricing", json={"entries": [entry(), entry()]})

    assert response.status_code == 422


def test_rates_can_be_cleared(api):
    api.put("/api/settings/pricing", json={"entries": [entry()]})

    response = api.put("/api/settings/pricing", json={"entries": []})

    assert response.status_code == 200
    assert response.json()["pricing"] == []
