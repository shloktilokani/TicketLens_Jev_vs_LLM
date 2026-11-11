"""Jev (System One) and Ollama adapters, tested against simulated HTTP replies (no network)."""

import json

import httpx
import pytest

from app.core.taxonomy import SUBCATEGORIES
from app.providers.base import ProviderFailure, build_input
from app.providers.jev import JevAdapter
from app.providers.ollama import OllamaAdapter
from app.providers.registry import get_adapter, provider_labels
from app.schemas.classification import NormalizedResult
from tests.test_providers import TICKET

DATA = build_input(TICKET)


def client(handler) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))


def jev(handler, **kw) -> JevAdapter:
    options = dict(
        base_url="http://127.0.0.1:11434",
        model="autotrust-jev:9b",
        api_key=None,
        threshold=0.5,
        timeout=5,
        label="AutoTrust JEV",
    )
    return JevAdapter(**(options | kw), client=client(handler))


def choice(value, confidence):
    return {
        "type": "choice",
        "choice": value,
        "confidence": confidence,
        "probabilities": {value: confidence},
    }


JEV_REPLY = {
    "model": "autotrust-jev:9b",
    "answers": {
        "category": choice("Returns & Refunds", 0.93),
        "subcategory": choice("Refund Delay", 0.81),
        "priority": choice("Medium", 0.6),
        "sentiment": choice("Negative", 0.88),
        "escalation": {"type": "noul", "noul": 0.2},
    },
    "usage": {"input_tokens": 900, "output_tokens": 12},
}


def two_step(seen: list):
    """Answers whichever step is asked: the main questions, or the subcategory follow-up."""

    def handler(request):
        seen.append(
            (str(request.url), request.headers.get("authorization"), json.loads(request.content))
        )
        return httpx.Response(200, json=JEV_REPLY)

    return handler


def test_jev_asks_category_first_then_only_that_categorys_subcategories():
    seen = []

    result = jev(two_step(seen)).classify(DATA)

    assert len(seen) == 2
    (url, auth, first), (_, _, second) = seen
    assert url == "http://127.0.0.1:11434/v1/systemone"
    assert auth is None  # local AutoTrust needs no key
    assert set(first["questions"]) == {"category", "priority", "sentiment", "escalation"}
    assert first["questions"]["escalation"]["type"] == "noul"
    assert set(second["questions"]) == {"subcategory"}
    options = second["questions"]["subcategory"]["criteria"]
    assert set(options) == set(SUBCATEGORIES["Returns & Refunds"])  # the category Jev chose
    assert 2 <= len(options) <= 16  # AutoTrust's limit for a choice question
    assert first["state"] == second["state"]
    assert "final_classification" not in json.dumps(seen)

    normalized = NormalizedResult(**result.output)
    assert (normalized.subcategory, normalized.escalation_required) == ("Refund Delay", False)
    assert normalized.confidence["category"] == 0.93
    assert normalized.confidence["subcategory"] == 0.81
    assert normalized.summary is None
    assert normalized.unsupported_fields == ["summary", "suggested_resolution"]
    assert result.actual_model == "autotrust-jev:9b"


def test_jev_counts_tokens_from_both_steps_and_stores_both_payloads():
    seen = []

    result = jev(two_step(seen)).classify(DATA)

    assert (result.usage.input_tokens, result.usage.output_tokens) == (1800, 24)
    assert result.usage.total_tokens == 1824
    assert result.usage.usage_source == "provider_reported"
    assert [len(step["questions"]) for step in result.request_payload["steps"]] == [4, 1]
    assert len(result.response_payload["steps"]) == 2


def test_jev_rejects_an_unknown_category_without_a_second_call():
    calls = []
    reply = {"answers": {"category": choice("Not A Category", 0.5)}, "usage": {}}

    def handler(request):
        calls.append(request)
        return httpx.Response(200, json=reply)

    with pytest.raises(ProviderFailure) as raised:
        jev(handler).classify(DATA)

    assert raised.value.kind == "invalid_response"
    assert len(calls) == 1
    assert raised.value.request_payload is not None


def test_jev_failure_in_the_second_step_keeps_the_first_steps_payload():
    first_step = iter([httpx.Response(200, json=JEV_REPLY)])
    broken = httpx.Response(500, json={"error": "boom"})  # stays broken through every retry

    with pytest.raises(ProviderFailure) as raised:
        jev(lambda request: next(first_step, broken)).classify(DATA)

    assert raised.value.kind == "server_error"
    assert len(raised.value.request_payload["steps"]) == 2
    assert len(raised.value.response_payload["steps"]) == 1


def test_jev_sends_the_key_when_one_is_configured():
    seen = {}

    def handler(request):
        seen["auth"] = request.headers.get("authorization")
        return httpx.Response(200, json=JEV_REPLY)

    jev(handler, base_url="https://api.typesafe.ai", api_key="ts-test").classify(DATA)

    assert seen["auth"] == "Bearer ts-test"


@pytest.mark.parametrize(("threshold", "expected"), [(0.5, False), (0.15, True)])
def test_jev_escalation_uses_the_threshold(threshold, expected):
    result = jev(lambda r: httpx.Response(200, json=JEV_REPLY), threshold=threshold).classify(DATA)

    assert result.output["escalation_required"] is expected


@pytest.mark.parametrize(
    ("reply", "kind"),
    [
        (httpx.Response(402, json={"detail": "no credits"}), "insufficient_credits"),
        (httpx.Response(401, json={"detail": "bad key"}), "auth"),
        (httpx.Response(200, json={"answers": {}}), "invalid_response"),
        (httpx.Response(200, text="not json"), "invalid_response"),
    ],
)
def test_jev_failures_are_safe(reply, kind):
    with pytest.raises(ProviderFailure) as raised:
        jev(lambda r: reply).classify(DATA)

    assert raised.value.kind == kind


def test_unreachable_and_slow_servers():
    def refuse(request):
        raise httpx.ConnectError("refused")

    def slow(request):
        raise httpx.ReadTimeout("slow")

    with pytest.raises(ProviderFailure) as down:
        jev(refuse).classify(DATA)
    with pytest.raises(ProviderFailure) as late:
        jev(slow).classify(DATA)

    assert (down.value.kind, late.value.kind) == ("network", "timeout")
    assert late.value.status.value == "Timed Out"


OLLAMA_OUTPUT = {
    "category": "Returns & Refunds",
    "subcategory": "Refund Delay",
    "priority": "High",
    "sentiment": "Negative",
    "escalation_required": False,
    "summary": "The customer's refund for returned headphones has not arrived.",
    "suggested_resolution": "Check the refund status and update the customer.",
}


def test_ollama_requests_structured_json_and_parses_it():
    seen = {}

    def handler(request):
        seen["url"] = str(request.url)
        seen["body"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={
                "model": "qwen3:8b",
                "message": {"role": "assistant", "content": json.dumps(OLLAMA_OUTPUT)},
                "prompt_eval_count": 700,
                "eval_count": 60,
            },
        )

    adapter = OllamaAdapter(
        base_url="http://127.0.0.1:11434", model="qwen3:8b", timeout=5, client=client(handler)
    )
    result = adapter.classify(DATA)

    assert seen["url"] == "http://127.0.0.1:11434/api/chat"
    body = seen["body"]
    assert body["format"]["properties"]["subcategory"]["enum"][0] == "Order Status"
    assert body["options"]["temperature"] == 0 and body["stream"] is False
    assert "final_classification" not in json.dumps(body)
    normalized = NormalizedResult(**result.output)
    assert normalized.summary.startswith("The customer's refund")
    assert (result.usage.input_tokens, result.usage.output_tokens, result.usage.total_tokens) == (
        700,
        60,
        760,
    )
    assert result.usage.usage_source == "provider_reported"


def test_ollama_non_json_reply_is_an_invalid_response():
    reply = {"model": "qwen3:8b", "message": {"content": "Sure! Here is the answer"}}
    adapter = OllamaAdapter(
        base_url="http://x",
        model="qwen3:8b",
        timeout=5,
        client=client(lambda r: httpx.Response(200, json=reply)),
    )

    with pytest.raises(ProviderFailure) as raised:
        adapter.classify(DATA)

    assert raised.value.kind == "invalid_response"


# --- registry ------------------------------------------------------------------------------


def test_registry_picks_local_models_and_needs_no_key(test_settings):
    settings = test_settings.model_copy(
        update={"jev_base_url": "http://127.0.0.1:11434", "jev_model": "autotrust-jev:9b"}
    )

    assert isinstance(get_adapter("jev", settings), JevAdapter)
    assert isinstance(get_adapter("gpt", settings), OllamaAdapter)
    assert provider_labels(settings) == {
        "jev": "AutoTrust JEV (local) · autotrust-jev:9b",
        "gpt": "Ollama (local) · qwen3:8b",
    }


def test_registry_needs_a_key_for_hosted_jev(test_settings):
    with pytest.raises(ProviderFailure) as raised:
        get_adapter("jev", test_settings)  # default base URL is TypeSafe's hosted API

    assert raised.value.kind == "not_configured"
    assert "TYPESAFE_API_KEY" in raised.value.message


def test_mock_mode_labels(test_settings):
    labels = provider_labels(test_settings.model_copy(update={"mock_providers": True}))

    assert labels == {"jev": "Fake AI", "gpt": "Fake AI"}
