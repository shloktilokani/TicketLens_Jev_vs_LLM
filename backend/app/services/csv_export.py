"""CSV exports of tickets, AI executions and comparisons.

Request/response payloads are left out. Secrets are never stored, so they can never be exported.
"""

import csv
import io
from datetime import datetime

from pymongo.database import Database

from app.repositories.database import find_all
from app.services.csv_import import LABEL_FIELDS

Columns = list[tuple[str, str]]  # (CSV header, dotted document path)

TICKETS: Columns = [
    ("ticket_id", "ticket_id"),
    ("title", "title"),
    ("description", "description"),
    ("customer_name", "customer.name"),
    ("customer_email", "customer.email"),
    ("order_id", "order.order_id"),
    ("product_name", "order.product_name"),
    ("submission_channel", "submission_channel"),
    ("status", "status"),
    *[(f"final_{f}", f"final_classification.{f}") for f in LABEL_FIELDS],
    ("final_manually_edited", "final_classification.manually_edited"),
    ("source_type", "source.type"),
    ("is_sample", "is_sample"),
    ("created_at", "created_at"),
    ("updated_at", "updated_at"),
]
EXECUTIONS: Columns = [
    *[
        (f, f)
        for f in (
            "execution_id",
            "ticket_id",
            "comparison_id",
            "provider",
            "requested_model",
            "actual_model",
            "status",
            "started_at",
            "completed_at",
            "duration_ms",
        )
    ],
    *[(f, f"usage.{f}") for f in ("input_tokens", "output_tokens", "total_tokens", "usage_source")],
    ("estimated_cost", "estimated_cost.amount"),
    ("currency", "estimated_cost.currency"),
    ("pricing_version", "pricing_snapshot.pricing_version"),
    *[(f, f"normalized_result.{f}") for f in LABEL_FIELDS],
    ("error_code", "error.code"),
    ("error_message", "error.message"),
    ("prompt_version", "prompt_version"),
    ("taxonomy_version", "taxonomy_version"),
]
COMPARISONS: Columns = [
    *[
        (f, f)
        for f in (
            "comparison_id",
            "ticket_id",
            "jev_execution_id",
            "gpt_execution_id",
            "status",
            "agreement_count",
            "comparable_field_count",
            "agreement_rate",
            "created_at",
        )
    ],
    *[
        (f"{f}_{side}", f"field_comparison.{f}.{side}")
        for f in LABEL_FIELDS
        for side in ("jev", "gpt", "match")
    ],
]
EXPORTS: dict[str, tuple[str, Columns, str]] = {
    "tickets": ("tickets", TICKETS, "created_at"),
    "executions": ("ai_executions", EXECUTIONS, "started_at"),
    "comparisons": ("comparisons", COMPARISONS, "created_at"),
}


def value_at(doc, path: str):
    for part in path.split("."):
        doc = doc.get(part) if isinstance(doc, dict) else None
    return doc


def cell(value) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    text = value.isoformat() if isinstance(value, datetime) else str(value)
    # Spreadsheet formula injection: Excel runs a cell starting with these as a formula.
    return "'" + text if text[:1] in ("=", "+", "-", "@", "\t", "\r") else text


def to_csv(docs: list[dict], columns: Columns) -> str:
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow([header for header, _ in columns])
    writer.writerows([cell(value_at(doc, path)) for _, path in columns] for doc in docs)
    return out.getvalue()


def export(db: Database, name: str) -> str:
    collection, columns, sort_field = EXPORTS[name]
    return to_csv(find_all(db, collection, sort_field), columns)
