import pytest
from fastapi.testclient import TestClient

from app.core import taxonomy as t
from app.main import create_app

SPEC_CATEGORIES = {
    "Orders & Delivery": [
        "Order Status",
        "Delayed Delivery",
        "Missing Package",
        "Wrong Item Delivered",
        "Address Change",
        "Delivery Attempt Failed",
        "Damaged in Transit",
    ],
    "Payments & Billing": [
        "Payment Failed",
        "Duplicate Charge",
        "Refund Status",
        "Invoice Request",
        "Payment Method",
        "Promotional Discount",
    ],
    "Returns & Refunds": [
        "Return Request",
        "Return Pickup",
        "Refund Delay",
        "Exchange Request",
        "Return Rejected",
        "Cancellation",
    ],
    "Product Issues": [
        "Defective Product",
        "Damaged Product",
        "Missing Parts",
        "Product Information",
        "Warranty",
        "Wrong Product",
    ],
    "Account & Login": [
        "Login Failure",
        "Password Reset",
        "Account Locked",
        "Profile Update",
        "Account Access",
        "Verification",
    ],
    "General Enquiries": ["Store Policy", "Product Availability", "Feedback", "Complaint", "Other"],
}


def test_taxonomy_matches_the_spec_exactly():
    assert t.TAXONOMY_VERSION == "1.0"
    assert {c: list(s) for c, s in t.SUBCATEGORIES.items()} == SPEC_CATEGORIES
    assert [c.value for c in t.Category] == list(SPEC_CATEGORIES)


def test_subcategory_names_are_unique_across_categories():
    names = [s for subs in t.SUBCATEGORIES.values() for s in subs]
    assert len(names) == len(set(names)) == 36


@pytest.mark.parametrize(
    ("enum", "values"),
    [
        (t.Priority, ["Critical", "High", "Medium", "Low"]),
        (t.Sentiment, ["Positive", "Neutral", "Negative"]),
        (t.TicketStatus, ["Open", "In Progress", "Resolved", "Closed"]),
        (t.Channel, ["Email", "Chat", "Phone", "Website"]),
        (t.Provider, ["jev", "gpt"]),
        (
            t.ExecutionStatus,
            ["Running", "Succeeded", "Failed", "Invalid Response", "Cancelled", "Timed Out"],
        ),
        (t.ComparisonStatus, ["Completed", "Partial", "Unavailable"]),
        (
            t.BulkJobStatus,
            ["Queued", "Running", "Completed", "Completed With Errors", "Interrupted", "Failed"],
        ),
    ],
)
def test_enums_hold_the_canonical_values(enum, values):
    assert [member.value for member in enum] == values


@pytest.mark.parametrize(
    ("category", "subcategory"),
    [(c, s) for c, subs in SPEC_CATEGORIES.items() for s in subs],
)
def test_every_spec_pair_is_valid(category, subcategory):
    assert t.is_valid_pair(category, subcategory)


@pytest.mark.parametrize(
    ("category", "subcategory"),
    [
        ("Payments & Billing", "Password Reset"),
        ("Orders & Delivery", "Refund Delay"),
        ("Unknown", "Other"),
        ("General Enquiries", "Not A Subcategory"),
        ("general enquiries", "Other"),
    ],
)
def test_inconsistent_or_unknown_pairs_are_invalid(category, subcategory):
    assert not t.is_valid_pair(category, subcategory)


def test_taxonomy_endpoint_serves_the_same_values(test_settings):
    with TestClient(create_app(test_settings)) as client:
        body = client.get("/api/taxonomy").json()

    assert body["version"] == "1.0"
    assert body["categories"] == SPEC_CATEGORIES
    assert body["priorities"] == ["Critical", "High", "Medium", "Low"]
    assert body["channels"] == ["Email", "Chat", "Phone", "Website"]
    assert body["statuses"] == ["Open", "In Progress", "Resolved", "Closed"]
