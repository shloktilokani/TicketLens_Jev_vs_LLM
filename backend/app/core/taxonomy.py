"""Canonical values shared by validation, providers, evaluation and the UI (via /api/taxonomy).

Changing a value here changes the contract: bump TAXONOMY_VERSION for category/subcategory changes.
"""

from enum import StrEnum

TAXONOMY_VERSION = "1.0"


class Category(StrEnum):
    ORDERS_DELIVERY = "Orders & Delivery"
    PAYMENTS_BILLING = "Payments & Billing"
    RETURNS_REFUNDS = "Returns & Refunds"
    PRODUCT_ISSUES = "Product Issues"
    ACCOUNT_LOGIN = "Account & Login"
    GENERAL_ENQUIRIES = "General Enquiries"


SUBCATEGORIES: dict[Category, tuple[str, ...]] = {
    Category.ORDERS_DELIVERY: (
        "Order Status",
        "Delayed Delivery",
        "Missing Package",
        "Wrong Item Delivered",
        "Address Change",
        "Delivery Attempt Failed",
        "Damaged in Transit",
    ),
    Category.PAYMENTS_BILLING: (
        "Payment Failed",
        "Duplicate Charge",
        "Refund Status",
        "Invoice Request",
        "Payment Method",
        "Promotional Discount",
    ),
    Category.RETURNS_REFUNDS: (
        "Return Request",
        "Return Pickup",
        "Refund Delay",
        "Exchange Request",
        "Return Rejected",
        "Cancellation",
    ),
    Category.PRODUCT_ISSUES: (
        "Defective Product",
        "Damaged Product",
        "Missing Parts",
        "Product Information",
        "Warranty",
        "Wrong Product",
    ),
    Category.ACCOUNT_LOGIN: (
        "Login Failure",
        "Password Reset",
        "Account Locked",
        "Profile Update",
        "Account Access",
        "Verification",
    ),
    Category.GENERAL_ENQUIRIES: (
        "Store Policy",
        "Product Availability",
        "Feedback",
        "Complaint",
        "Other",
    ),
}


class Priority(StrEnum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class Sentiment(StrEnum):
    POSITIVE = "Positive"
    NEUTRAL = "Neutral"
    NEGATIVE = "Negative"


class TicketStatus(StrEnum):
    OPEN = "Open"
    IN_PROGRESS = "In Progress"
    RESOLVED = "Resolved"
    CLOSED = "Closed"


class Channel(StrEnum):
    EMAIL = "Email"
    CHAT = "Chat"
    PHONE = "Phone"
    WEBSITE = "Website"


class Provider(StrEnum):
    JEV = "jev"
    GPT = "gpt"


class ExecutionStatus(StrEnum):
    RUNNING = "Running"  # in progress; not in requirements.md's list (see PROGRESS.md assumptions)
    SUCCEEDED = "Succeeded"
    FAILED = "Failed"
    INVALID_RESPONSE = "Invalid Response"
    CANCELLED = "Cancelled"
    TIMED_OUT = "Timed Out"


class ComparisonStatus(StrEnum):
    COMPLETED = "Completed"
    PARTIAL = "Partial"
    UNAVAILABLE = "Unavailable"


class BulkJobStatus(StrEnum):
    QUEUED = "Queued"
    RUNNING = "Running"
    COMPLETED = "Completed"
    COMPLETED_WITH_ERRORS = "Completed With Errors"
    INTERRUPTED = "Interrupted"
    FAILED = "Failed"


# The taxonomy in force. Settings can replace it; each change gets a new version.
# shortcut: held per process, which fits the one documented backend process; several workers would
# need to re-read it from MongoDB.
_active = {
    "version": TAXONOMY_VERSION,
    "categories": {c.value: subs for c, subs in SUBCATEGORIES.items()},
}


def set_active(version: str, categories: dict[str, list[str]]) -> None:
    _active.update(version=version, categories={c: tuple(s) for c, s in categories.items()})


def reset() -> None:
    set_active(TAXONOMY_VERSION, {c.value: list(s) for c, s in SUBCATEGORIES.items()})


def active_version() -> str:
    return _active["version"]


def active_categories() -> dict[str, tuple[str, ...]]:
    return _active["categories"]


def is_valid_pair(category: str, subcategory: str) -> bool:
    """True only when the subcategory belongs to the category. Matching is exact, never fuzzy."""
    return subcategory in active_categories().get(category, ())


def as_dict() -> dict:
    """Every canonical value, in display order, for the frontend."""
    return {
        "version": active_version(),
        "categories": {category: list(subs) for category, subs in active_categories().items()},
        "priorities": [p.value for p in Priority],
        "sentiments": [s.value for s in Sentiment],
        "statuses": [s.value for s in TicketStatus],
        "channels": [c.value for c in Channel],
        "providers": [p.value for p in Provider],
        "execution_statuses": [s.value for s in ExecutionStatus],
    }
