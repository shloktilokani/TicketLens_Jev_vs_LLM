"""Jev through the System One decision API (architecture.md section 4).

The same request works for TypeSafe's hosted Jev (https://api.typesafe.ai, API key required) and
for AutoTrust's open JEV models served locally by Ollama (http://127.0.0.1:11434, no key).
Jev returns typed decisions only, so summary and suggested resolution are unsupported.
"""

import httpx

from app.providers import definitions as d
from app.providers.base import ProviderFailure, ProviderInput, ProviderResult
from app.providers.http import post_json
from app.schemas.executions import Usage

CHOICE_QUESTIONS = {
    "category": ("Which support category best fits this ticket?", d.CATEGORY),
    "subcategory": ("Which subcategory best fits this ticket?", d.SUBCATEGORY),
    "priority": ("How urgent is this ticket?", d.PRIORITY),
    "sentiment": ("What is the customer's sentiment?", d.SENTIMENT),
}


def build_request(model: str, data: ProviderInput) -> dict:
    questions = {
        name: {"type": "choice", "instructions": f"{d.INSTRUCTIONS} {text}", "criteria": criteria}
        for name, (text, criteria) in CHOICE_QUESTIONS.items()
    }
    questions["escalation"] = {
        "type": "noul",
        "instructions": "Does this ticket need escalation to a human specialist?",
        "criteria": {"true": d.ESCALATION, "false": "A routine issue that support can handle."},
    }
    state = data.model_dump(
        include={
            "title",
            "description",
            "order_id",
            "product_name",
            "submission_channel",
            "language",
        }
    )
    return {"model": model, "state": state, "questions": questions}


def parse_output(answers: dict, threshold: float) -> dict:
    """Map System One answers to the normalized fields; keep each choice's own confidence."""
    try:
        output = {name: answers[name]["choice"] for name in CHOICE_QUESTIONS}
        confidence = {name: answers[name]["confidence"] for name in CHOICE_QUESTIONS}
        yes = float(answers["escalation"]["noul"])
    except (KeyError, TypeError, ValueError):
        raise ProviderFailure(
            "invalid_response", "Jev's answer was missing expected fields."
        ) from None
    return output | {
        "escalation_required": yes >= threshold,
        "confidence": confidence | {"escalation_required": max(yes, 1 - yes)},
        "unsupported_fields": ["summary", "suggested_resolution"],
    }


class JevAdapter:
    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        api_key: str | None,
        threshold: float,
        timeout: float,
        label: str,
        client: httpx.Client | None = None,
    ):
        self.url = base_url.rstrip("/") + "/v1/systemone"
        self.model, self.api_key, self.threshold = model, api_key, threshold
        self.timeout, self.label, self.client = timeout, label, client

    def classify(self, data: ProviderInput) -> ProviderResult:
        request = build_request(self.model, data)
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        response = post_json(
            self.url,
            request,
            label=self.label,
            timeout=self.timeout,
            headers=headers,
            client=self.client,
        )
        try:
            output = parse_output(response.get("answers") or {}, self.threshold)
        except ProviderFailure as failure:
            failure.request_payload, failure.response_payload = request, response
            raise
        usage = response.get("usage") or {}
        tokens_in, tokens_out = usage.get("input_tokens"), usage.get("output_tokens")
        return ProviderResult(
            requested_model=self.model,
            actual_model=response.get("model"),
            request_payload=request,
            response_payload=response,
            output=output,
            usage=Usage(
                input_tokens=tokens_in,
                output_tokens=tokens_out,
                total_tokens=None
                if tokens_in is None or tokens_out is None
                else tokens_in + tokens_out,
                usage_source="provider_reported" if usage else "unavailable",
            ),
        )
