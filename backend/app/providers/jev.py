"""Jev through the System One decision API (architecture.md section 4).

The same requests work for TypeSafe's hosted Jev (https://api.typesafe.ai, API key required) and
for AutoTrust's open JEV models served locally by Ollama (http://127.0.0.1:11434, no key).
Jev returns typed decisions only, so summary and suggested resolution are unsupported.

It takes two steps because AutoTrust allows 2-16 options per choice question and the taxonomy has
36 subcategories: first the category and the other fields, then only that category's subcategories.
This also means Jev cannot return a mismatched category and subcategory.
"""

import httpx

from app.core.taxonomy import active_categories
from app.providers import definitions as d
from app.providers.base import ProviderFailure, ProviderInput, ProviderResult
from app.providers.http import post_json
from app.schemas.executions import Usage

FIXED_QUESTIONS = {
    "priority": ("How urgent is this ticket?", d.PRIORITY),
    "sentiment": ("What is the customer's sentiment?", d.SENTIMENT),
}
CHOICE_NAMES = ["category", *FIXED_QUESTIONS]
STATE_FIELDS = {
    "title",
    "description",
    "order_id",
    "product_name",
    "submission_channel",
    "language",
}


def choice(text: str, criteria: dict, instructions: str = d.INSTRUCTIONS) -> dict:
    return {"type": "choice", "instructions": f"{instructions} {text}", "criteria": criteria}


def build_request(model: str, data: ProviderInput) -> dict:
    """Step 1: category, priority, sentiment and escalation."""
    rule = data.instructions
    questions = {
        "category": choice(
            "Which support category best fits this ticket?", d.category_criteria(), rule
        )
    }
    for name, (text, crit) in FIXED_QUESTIONS.items():
        questions[name] = choice(text, crit, rule)
    questions["escalation"] = {
        "type": "noul",
        "instructions": "Does this ticket need escalation to a human specialist?",
        "criteria": {"true": d.ESCALATION, "false": "A routine issue that support can handle."},
    }
    return {"model": model, "state": data.model_dump(include=STATE_FIELDS), "questions": questions}


def build_subcategory_request(model: str, data: ProviderInput, category: str) -> dict:
    """Step 2: only the subcategories of the category chosen in step 1."""
    criteria = d.subcategory_criteria()
    options = {sub: criteria[sub] for sub in active_categories()[category]}
    question = choice(
        f"This is a {category} ticket. Which subcategory fits best?", options, data.instructions
    )
    return {
        "model": model,
        "state": data.model_dump(include=STATE_FIELDS),
        "questions": {"subcategory": question},
    }


def parse_output(answers: dict, threshold: float) -> dict:
    """Map System One answers to the normalized fields; keep each choice's own confidence."""
    names = [*CHOICE_NAMES, "subcategory"]
    try:
        output = {name: answers[name]["choice"] for name in names}
        confidence = {name: answers[name]["confidence"] for name in names}
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


def total_usage(responses: list[dict]) -> Usage:
    """Tokens across both steps. Reported only if every step reported them; never estimated."""
    usages = [r.get("usage") or {} for r in responses]
    tokens_in = [u.get("input_tokens") for u in usages]
    tokens_out = [u.get("output_tokens") for u in usages]
    if None in tokens_in or None in tokens_out:
        return Usage()
    return Usage(
        input_tokens=sum(tokens_in),
        output_tokens=sum(tokens_out),
        total_tokens=sum(tokens_in) + sum(tokens_out),
        usage_source="provider_reported",
    )


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

    def post(self, request: dict) -> dict:
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        return post_json(
            self.url,
            request,
            label=self.label,
            timeout=self.timeout,
            headers=headers,
            client=self.client,
        )

    def run_steps(self, data: ProviderInput, requests: list[dict], responses: list[dict]) -> None:
        """Fill `requests` and `responses` as it goes, so a failure can still report them."""
        requests.append(build_request(self.model, data))
        responses.append(self.post(requests[0]))
        answers = responses[0].get("answers") or {}
        category = (answers.get("category") or {}).get("choice")
        if category not in active_categories():
            raise ProviderFailure("invalid_response", f"Jev chose an unknown category: {category}")
        requests.append(build_subcategory_request(self.model, data, category))
        responses.append(self.post(requests[1]))

    def classify(self, data: ProviderInput) -> ProviderResult:
        requests: list[dict] = []
        responses: list[dict] = []
        try:
            self.run_steps(data, requests, responses)
            answers = {**responses[0].get("answers", {}), **responses[1].get("answers", {})}
            output = parse_output(answers, self.threshold)
        except ProviderFailure as failure:
            failure.request_payload = {"steps": requests}
            failure.response_payload = {"steps": responses}
            raise
        return ProviderResult(
            requested_model=self.model,
            actual_model=responses[0].get("model"),
            request_payload={"steps": requests},
            response_payload={"steps": responses},
            output=output,
            usage=total_usage(responses),
        )
