"""The LLM side through a local Ollama model, with a JSON schema that forces valid enum values.

Same definitions as Jev (providers/definitions.py). Summaries and resolutions are in English.
"""

import json

import httpx

from app.core.taxonomy import Priority, Sentiment, active_categories
from app.providers import definitions as d
from app.providers.base import ProviderFailure, ProviderInput, ProviderResult
from app.providers.http import post_json
from app.schemas.executions import Usage


def schema() -> dict:
    """Built per request, because Settings can change the taxonomy."""
    return {
        "type": "object",
        "properties": {
            "category": {"type": "string", "enum": list(active_categories())},
            "subcategory": {"type": "string", "enum": list(d.subcategory_criteria())},
            "priority": {"type": "string", "enum": [p.value for p in Priority]},
            "sentiment": {"type": "string", "enum": [s.value for s in Sentiment]},
            "escalation_required": {"type": "boolean"},
            "summary": {"type": "string"},
            "suggested_resolution": {"type": "string"},
        },
        "required": [
            "category",
            "subcategory",
            "priority",
            "sentiment",
            "escalation_required",
            "summary",
            "suggested_resolution",
        ],
    }


def system_prompt(instructions: str = d.INSTRUCTIONS) -> str:
    lines = [
        instructions,
        "Write the summary and the suggested resolution in English, in one or two sentences each.",
        "Never claim an action has already been taken.",
        "Categories: " + json.dumps(d.category_criteria()),
        "Priority: " + json.dumps(d.PRIORITY),
        "Sentiment: " + json.dumps(d.SENTIMENT),
        "Escalation: " + d.ESCALATION,
        "Reply with JSON matching the given schema.",
    ]
    return "\n".join(lines)


def build_request(model: str, data: ProviderInput) -> dict:
    ticket = data.model_dump(
        include={
            "title",
            "description",
            "order_id",
            "product_name",
            "submission_channel",
            "language",
        }
    )
    return {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt(data.instructions)},
            {"role": "user", "content": json.dumps(ticket, ensure_ascii=False)},
        ],
        "format": schema(),
        "stream": False,
        "think": False,  # answer directly; thinking traces are not needed for classification
        "options": {"temperature": 0},
    }


class OllamaAdapter:
    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        timeout: float,
        client: httpx.Client | None = None,
    ):
        self.url = base_url.rstrip("/") + "/api/chat"
        self.model, self.timeout, self.client = model, timeout, client
        self.label = f"Ollama ({model})"

    def classify(self, data: ProviderInput) -> ProviderResult:
        request = build_request(self.model, data)
        response = post_json(
            self.url, request, label=self.label, timeout=self.timeout, client=self.client
        )
        try:
            output = json.loads(response["message"]["content"])
        except (KeyError, TypeError, ValueError):
            raise ProviderFailure(
                "invalid_response",
                f"{self.label} did not return the expected JSON.",
                request_payload=request,
                response_payload=response,
            ) from None
        tokens_in, tokens_out = response.get("prompt_eval_count"), response.get("eval_count")
        reported = tokens_in is not None or tokens_out is not None
        return ProviderResult(
            requested_model=self.model,
            actual_model=response.get("model"),
            request_payload=request,
            response_payload=response,
            output=output if isinstance(output, dict) else {},
            usage=Usage(
                input_tokens=tokens_in,
                output_tokens=tokens_out,
                total_tokens=(tokens_in or 0) + (tokens_out or 0) if reported else None,
                usage_source="provider_reported" if reported else "unavailable",
            ),
        )
