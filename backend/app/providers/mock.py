"""Fake Jev and LLM for tests and UI work: no network, no cost, deterministic.

Enabled only with MOCK_PROVIDERS=true. Models are named mock-jev / mock-gpt so a mock result can
never pass for a real one, and usage is reported as unavailable because token counts are never
invented. Put [mock-fail], [mock-timeout] or [mock-invalid] in a ticket title to simulate failures.
"""

import time

from app.core.taxonomy import Provider
from app.providers.base import ProviderFailure, ProviderInput, ProviderResult
from app.schemas.executions import Usage

# First matching keyword wins.
RULES = [
    ("charged twice", "Payments & Billing", "Duplicate Charge"),
    ("refund", "Returns & Refunds", "Refund Delay"),
    ("return", "Returns & Refunds", "Return Request"),
    ("payment", "Payments & Billing", "Payment Failed"),
    ("password", "Account & Login", "Password Reset"),
    ("log in", "Account & Login", "Login Failure"),
    ("login", "Account & Login", "Login Failure"),
    ("damaged", "Product Issues", "Damaged Product"),
    ("warranty", "Product Issues", "Warranty"),
    ("deliver", "Orders & Delivery", "Delayed Delivery"),
    ("order", "Orders & Delivery", "Order Status"),
]
URGENT = ("urgent", "immediately", "fraud", "hacked", "unauthorised", "unauthorized")
NEGATIVE = ("not ", "never", "late", "broken", "wrong", "angry", "disappointed", "worst", "still")


class MockProvider:
    def __init__(self, provider: str, delay_seconds: float = 0.0):
        self.provider = Provider(provider)
        self.model = f"mock-{self.provider.value}"
        self.delay_seconds = delay_seconds

    def classify(self, data: ProviderInput) -> ProviderResult:
        # Fake thinking time so the UI timers have something to show; the LLM takes twice as long.
        time.sleep(self.delay_seconds * (1 if self.provider is Provider.JEV else 2))
        title = data.title.lower()
        if "[mock-fail]" in title:
            raise ProviderFailure(
                "server_error",
                "Mock provider simulated a server error.",
                http_status=500,
                retryable=True,
            )
        if "[mock-timeout]" in title:
            raise ProviderFailure("timeout", "Mock provider simulated a timeout.", retryable=True)

        text = f"{data.title} {data.description}".lower()
        category, subcategory = next(
            ((c, s) for keyword, c, s in RULES if keyword in text), ("General Enquiries", "Other")
        )
        if "[mock-invalid]" in title:
            subcategory = "Not A Real Subcategory"  # fails taxonomy validation on purpose
        urgent = any(word in text for word in URGENT)
        output = {
            "category": category,
            "subcategory": subcategory,
            "priority": "High" if urgent else "Medium",
            "sentiment": "Negative" if any(word in text for word in NEGATIVE) else "Neutral",
            "escalation_required": urgent,
        }
        if self.provider is Provider.JEV:
            # Jev returns typed decisions only; it never writes free text.
            output |= {
                "confidence": {"category": 0.9, "subcategory": 0.8, "priority": 0.7},
                "unsupported_fields": ["summary", "suggested_resolution"],
            }
        else:
            output |= {
                "summary": f"Mock summary: {data.title}",
                "suggested_resolution": "Mock suggestion: review the ticket and reply.",
            }
        return ProviderResult(
            requested_model=self.model,
            actual_model=self.model,
            request_payload={"mock": True, "input": data.model_dump()},
            response_payload={"mock": True, "output": output},
            output=output,
            usage=Usage(),
        )
