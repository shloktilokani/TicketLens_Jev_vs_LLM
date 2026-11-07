"""The contract every provider adapter follows (architecture.md section 3).

An adapter owns authentication, the provider's request shape, response parsing, usage extraction
and turning provider errors into a safe ProviderFailure. Everything else is the service's job.
"""

from typing import Literal, Protocol

from pydantic import BaseModel

from app.core import taxonomy
from app.core.taxonomy import ExecutionStatus
from app.schemas.executions import Usage

PROMPT_VERSION = "1.0"

FailureKind = Literal[
    "not_configured",
    "invalid_request",
    "auth",
    "insufficient_credits",
    "rate_limited",
    "server_error",
    "timeout",
    "network",
    "invalid_response",
    "unexpected",
]


class ProviderInput(BaseModel):
    """Exactly what both providers see. Built only by build_input()."""

    ticket_id: str
    title: str
    description: str
    order_id: str | None
    product_name: str | None
    submission_channel: str
    language: str = "English"
    taxonomy_version: str
    categories: dict[str, list[str]]
    priorities: list[str]
    sentiments: list[str]


def build_input(ticket: dict) -> ProviderInput:
    """Pick the allowed ticket fields. Labels, earlier results, the final classification, notes and
    customer contact details never reach a provider (AGENTS.md section 3)."""
    canon = taxonomy.as_dict()
    return ProviderInput(
        ticket_id=ticket["ticket_id"],
        title=ticket["title"],
        description=ticket["description"],
        order_id=ticket["order"]["order_id"],
        product_name=ticket["order"]["product_name"],
        submission_channel=ticket["submission_channel"],
        taxonomy_version=canon["version"],
        categories=canon["categories"],
        priorities=canon["priorities"],
        sentiments=canon["sentiments"],
    )


class ProviderResult(BaseModel):
    """An adapter's answer before validation. `output` is checked against NormalizedResult."""

    requested_model: str
    actual_model: str | None
    request_payload: dict
    response_payload: dict | None
    output: dict
    usage: Usage


class ProviderFailure(Exception):
    """A provider attempt that failed. `message` is safe to show the operator."""

    def __init__(
        self,
        kind: FailureKind,
        message: str,
        *,
        http_status: int | None = None,
        retryable: bool = False,
        request_payload: dict | None = None,
        response_payload: dict | None = None,
    ):
        super().__init__(message)
        self.kind = kind
        self.message = message
        self.http_status = http_status
        self.retryable = retryable
        self.request_payload = request_payload
        self.response_payload = response_payload

    @property
    def status(self) -> ExecutionStatus:
        if self.kind == "timeout":
            return ExecutionStatus.TIMED_OUT
        if self.kind == "invalid_response":
            return ExecutionStatus.INVALID_RESPONSE
        return ExecutionStatus.FAILED


MESSAGES = {
    "invalid_request": "{p} rejected the request as invalid.",
    "auth": "{p} rejected the API key. Check it in backend/.env.",
    "insufficient_credits": "{p} reports insufficient credits. Add credits to the account.",
    "rate_limited": "{p} is limiting requests. Try again shortly.",
    "server_error": "{p} had a server error. Try again later.",
}


def failure_for_status(provider_label: str, status: int) -> ProviderFailure:
    """Map an HTTP error to a failure (ai-evaluation.md section 12). Only 429 and 5xx retry."""
    if status in (401, 403):
        kind = "auth"
    elif status == 402:
        kind = "insufficient_credits"
    elif status == 429:
        kind = "rate_limited"
    elif status >= 500:
        kind = "server_error"
    else:
        kind = "invalid_request"
    return ProviderFailure(
        kind,
        MESSAGES[kind].format(p=provider_label),
        http_status=status,
        retryable=kind in ("rate_limited", "server_error"),
    )


class Adapter(Protocol):
    def classify(self, data: ProviderInput) -> ProviderResult: ...
