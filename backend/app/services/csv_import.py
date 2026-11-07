"""CSV ticket import: row-level validation, duplicate detection and separate evaluation labels.

Valid rows are imported even when other rows fail. AI never runs on imported tickets.
"""

import csv
import hashlib
import io
from uuid import uuid4

from pydantic import ValidationError
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError

from app.core.clock import utc_now
from app.core.taxonomy import (
    SUBCATEGORIES,
    TAXONOMY_VERSION,
    Category,
    Channel,
    Priority,
    Sentiment,
)
from app.repositories import labels
from app.repositories import tickets as ticket_repo
from app.schemas.classification import Classification
from app.schemas.imports import ImportRowError, ImportSummary
from app.schemas.tickets import TicketCreate
from app.services import tickets as ticket_service

TICKET_COLUMNS = [
    "title",
    "description",
    "customer_name",
    "customer_email",
    "order_id",
    "product_name",
    "submission_channel",
]
LABEL_FIELDS = ["category", "subcategory", "priority", "sentiment", "escalation_required"]
COLUMNS = TICKET_COLUMNS + [f"expected_{f}" for f in LABEL_FIELDS]  # = sample_tickets_template.csv
REQUIRED_COLUMNS = {"title", "description", "customer_name", "customer_email", "submission_channel"}
DATASET_VERSION = "shopkart-synthetic-v1"
MAX_ROWS = 5000
PREVIEW_ROWS = 5

# Case-insensitive lookup to canonical values, so "email" or "EMAIL" becomes "Email".
CANONICAL = {
    field: {value.lower(): value for value in values}
    for field, values in {
        "submission_channel": [c.value for c in Channel],
        "category": [c.value for c in Category],
        "subcategory": [s for subs in SUBCATEGORIES.values() for s in subs],
        "priority": [p.value for p in Priority],
        "sentiment": [s.value for s in Sentiment],
    }.items()
}
BOOLEANS = {"true": True, "yes": True, "1": True, "false": False, "no": False, "0": False}
FRIENDLY = {
    "string_too_short": "is required",
    "missing": "is required",
    "string_pattern_mismatch": "is not a valid email address",
}


class CsvFileError(ValueError):
    """The file as a whole cannot be read, so nothing is imported."""


def normalize(field: str, raw: str):
    """Collapse whitespace and map enum-like values to canonical form. Descriptions stay exact."""
    if field == "description":
        return raw
    value = " ".join(raw.split())
    if field in CANONICAL:
        return CANONICAL[field].get(value.lower(), value)  # unknown values fail validation later
    if field == "escalation_required":
        return BOOLEANS.get(value.lower(), value)
    return value


def fingerprint(ticket: TicketCreate) -> str:
    """Stable identity for duplicate detection, insensitive to case and spacing."""
    parts = [ticket.title, ticket.description, ticket.customer_email, ticket.order_id or ""]
    return hashlib.sha256(
        "\x1f".join(" ".join(p.lower().split()) for p in parts).encode()
    ).hexdigest()


def read_rows(content: bytes) -> list[dict[str, str]]:
    try:
        text = content.decode("utf-8-sig")  # -sig drops a byte-order mark if present
    except UnicodeDecodeError:
        raise CsvFileError(
            "The file is not UTF-8 text. Save it as CSV UTF-8 and try again."
        ) from None
    reader = csv.DictReader(io.StringIO(text))
    missing = REQUIRED_COLUMNS - {(name or "").strip() for name in reader.fieldnames or []}
    if missing:
        raise CsvFileError(f"Missing required column(s): {', '.join(sorted(missing))}.")
    rows = [{(k or "").strip(): v for k, v in row.items() if isinstance(v, str)} for row in reader]
    if not rows:
        raise CsvFileError("The file has a header but no data rows.")
    if len(rows) > MAX_ROWS:
        raise CsvFileError(f"The file has {len(rows)} rows; the limit is {MAX_ROWS}.")
    return rows


def row_errors(exc: ValidationError, row: int, prefix: str, fallback: str) -> list[ImportRowError]:
    return [
        ImportRowError(
            row=row,
            field=prefix + str(e["loc"][0]) if e["loc"] else prefix + fallback,
            message=FRIENDLY.get(e["type"], e["msg"].removeprefix("Value error, ")),
        )
        for e in exc.errors()
    ]


def validate_row(row: dict[str, str], number: int):
    """Return (ticket, label, errors). The label is None for an unlabelled row."""
    errors: list[ImportRowError] = []
    ticket = label = None
    try:
        ticket = TicketCreate(**{c: normalize(c, row.get(c, "")) for c in TICKET_COLUMNS})
    except ValidationError as exc:
        errors += row_errors(exc, number, "", "title")

    expected = {f: normalize(f, row.get(f"expected_{f}", "")) for f in LABEL_FIELDS}
    filled = [f for f, v in expected.items() if v != ""]
    if 0 < len(filled) < len(LABEL_FIELDS):
        errors.append(
            ImportRowError(
                row=number, field="expected_*", message="fill all five expected_ columns or none"
            )
        )
    elif filled:
        try:
            label = Classification(**expected)
        except ValidationError as exc:
            errors += row_errors(exc, number, "expected_", "subcategory")
    return ticket, label, errors


def save(
    db: Database, ticket: TicketCreate, label: Classification | None, fp: str, batch: str
) -> str:
    source = {"type": "csv_import", "import_batch_id": batch, "source_fingerprint": fp}
    doc = ticket_service.create(db, ticket, source=source, is_sample=label is not None)
    if label:
        labels.insert(
            db,
            {
                "ticket_id": doc["ticket_id"],
                "taxonomy_version": TAXONOMY_VERSION,
                "expected": label.model_dump(),
                "dataset_version": DATASET_VERSION,
                "created_at": utc_now(),
            },
        )
    return doc["ticket_id"]


def import_csv(db: Database, content: bytes, *, dry_run: bool) -> ImportSummary:
    rows = read_rows(content)
    summary = ImportSummary(dry_run=dry_run, total_rows=len(rows))
    batch, seen = f"imp_{uuid4().hex}", set()
    for number, row in enumerate(rows, start=1):
        ticket, label, errors = validate_row(row, number)
        if errors:
            summary.invalid += 1
            summary.errors += errors
            continue
        fp = fingerprint(ticket)
        duplicate = fp in seen or ticket_repo.fingerprint_exists(db, fp)
        seen.add(fp)
        try:
            if not duplicate and not dry_run:
                summary.imported_ticket_ids.append(save(db, ticket, label, fp, batch))
        except DuplicateKeyError:  # a concurrent import stored the same row first
            duplicate = True
        if duplicate:
            summary.duplicates_skipped += 1
            summary.duplicate_rows.append(number)
            continue
        summary.imported += 1
        if dry_run and len(summary.preview) < PREVIEW_ROWS:
            summary.preview.append(ticket.model_dump() | {"labelled": label is not None})
    return summary
