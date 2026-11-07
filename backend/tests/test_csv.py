import csv
import io
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.services.csv_import import COLUMNS

CONTEXT = Path(__file__).resolve().parents[2] / ".context"
HEADER = ",".join(COLUMNS)
VALID = "Refund late,My refund is late.,Aarav Mehta,aarav@example.test,ORD-1,Headphones,Website"
LABELS = "Returns & Refunds,Refund Delay,Medium,Negative,false"


@pytest.fixture
def api(test_settings, test_db):
    with TestClient(create_app(test_settings)) as client:
        yield client


def upload(api, text: str | bytes, dry_run: bool = False):
    body = text.encode() if isinstance(text, str) else text
    return api.post(
        "/api/imports/tickets",
        params={"dry_run": dry_run},
        content=body,
        headers={"Content-Type": "text/csv"},
    )


def csv_of(*rows: str) -> str:
    return "\n".join([HEADER, *rows]) + "\n"


def errors_by_row(summary) -> dict[int, set[str]]:
    found: dict[int, set[str]] = {}
    for e in summary["errors"]:
        found.setdefault(e["row"], set()).add(e["field"])
    return found


# --- template ------------------------------------------------------------------------------


def test_template_matches_the_spec_file(api):
    spec_header = (CONTEXT / "sample_tickets_template.csv").read_text().splitlines()[0]

    response = api.get("/api/imports/template")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "attachment" in response.headers["content-disposition"]
    assert response.text.strip() == spec_header.strip() == HEADER


# --- mixed file ----------------------------------------------------------------------------


MIXED = csv_of(
    f"{VALID},{LABELS}",  # 1 valid, labelled
    "Login broken,Cannot log in.,Diya Shah,diya@example.test,,,chat,,,,,",  # 2 valid, unlabelled
    ",No title here.,Kabir,kabir@example.test,,,Email,,,,,",  # 3 missing title
    "Bad email,Text.,Isha,not-an-email,,,Email,,,,,",  # 4 invalid email
    "Fax ticket,Text.,Arjun,arjun@example.test,,,Fax,,,,,",  # 5 unknown channel
    # 6: Password Reset is not a Payments & Billing subcategory
    "Wrong pair,Text.,Meera,meera@example.test,,,Email,"
    "Payments & Billing,Password Reset,High,Negative,false",
    # 7: only one of the five expected_ columns is filled
    "Half labelled,Text.,Rohan,rohan@example.test,,,Email,Returns & Refunds,,,,",
    f"{VALID},{LABELS}",  # 8 duplicate of row 1 in the same file
)


def test_mixed_file_reports_accurate_counts(api, test_db):
    summary = upload(api, MIXED).json()

    assert (
        summary["total_rows"],
        summary["imported"],
        summary["invalid"],
        summary["duplicates_skipped"],
    ) == (
        8,
        2,
        5,
        1,
    )
    assert summary["duplicate_rows"] == [8]
    assert errors_by_row(summary) == {
        3: {"title"},
        4: {"customer_email"},
        5: {"submission_channel"},
        6: {"expected_subcategory"},
        7: {"expected_*"},
    }
    assert test_db.tickets.count_documents({}) == 2


def test_valid_rows_are_stored_with_import_source_and_normalised_values(api, test_db):
    summary = upload(api, MIXED).json()

    first, second = (
        test_db.tickets.find_one({"ticket_id": i}) for i in summary["imported_ticket_ids"]
    )
    assert first["source"]["type"] == "csv_import"
    assert first["source"]["source_fingerprint"]
    assert first["is_sample"] is True
    assert second["submission_channel"] == "Chat"  # "chat" was normalised
    assert second["is_sample"] is False


def test_labels_are_stored_separately_from_tickets(api, test_db):
    summary = upload(api, MIXED).json()

    labelled = summary["imported_ticket_ids"][0]
    label = test_db.evaluation_labels.find_one({"ticket_id": labelled})
    assert label["expected"]["subcategory"] == "Refund Delay"
    assert label["dataset_version"] == "shopkart-synthetic-v1"
    assert test_db.evaluation_labels.count_documents({}) == 1
    ticket = test_db.tickets.find_one({"ticket_id": labelled}, {"_id": 0})
    assert "expected" not in str(ticket).lower()


def test_reimporting_the_same_file_skips_every_row(api, test_db):
    upload(api, MIXED)

    summary = upload(api, MIXED).json()

    assert (summary["imported"], summary["duplicates_skipped"], summary["invalid"]) == (0, 3, 5)
    assert test_db.tickets.count_documents({}) == 2


def test_dry_run_reports_without_writing(api, test_db):
    summary = upload(api, MIXED, dry_run=True).json()

    assert summary["dry_run"] is True
    assert summary["imported"] == 2
    assert [p["title"] for p in summary["preview"]] == ["Refund late", "Login broken"]
    assert test_db.tickets.count_documents({}) == 0
    assert test_db.counters.count_documents({}) == 0


def test_import_never_runs_ai(api, test_db):
    upload(api, MIXED)

    assert test_db.ai_executions.count_documents({}) == 0
    assert test_db.comparisons.count_documents({}) == 0


def test_bom_crlf_and_quoted_multiline_description(api, test_db):
    text = HEADER + '\r\n"Two lines","First line\r\nSecond line",A,a@example.test,,,Email,,,,,\r\n'

    summary = upload(api, "﻿" + text).json()

    assert summary["imported"] == 1
    assert test_db.tickets.find_one()["description"] == "First line\r\nSecond line"


@pytest.mark.parametrize(
    ("body", "status"),
    [
        ("", 400),
        ("title,description\nOnly two,columns\n", 400),
        (HEADER + "\n", 400),
        (b"\xff\xfe\x00bad", 400),
    ],
)
def test_unreadable_files_are_rejected_whole(api, body, status):
    assert upload(api, body).status_code == status


def test_oversized_file_is_rejected(api):
    big = csv_of(*[VALID + ",,,,," for _ in range(1)]) + "x" * (5 * 1024 * 1024)

    assert upload(api, big).status_code == 413


def test_supplied_100_ticket_sample_is_valid(api):
    content = (CONTEXT / "sample_tickets_100.csv").read_bytes()

    summary = upload(api, content, dry_run=True).json()

    assert (summary["total_rows"], summary["imported"], summary["invalid"]) == (100, 100, 0)


# --- exports -------------------------------------------------------------------------------


def read_csv(response) -> list[dict]:
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    return list(csv.DictReader(io.StringIO(response.text)))


def test_ticket_export_is_valid_csv_and_neutralises_formulas(api):
    upload(api, csv_of("=HYPERLINK(1),Text.,Name,n@example.test,,,Email,,,,,"))

    rows = read_csv(api.get("/api/exports/tickets.csv"))

    assert len(rows) == 1
    assert rows[0]["title"] == "'=HYPERLINK(1)"
    assert rows[0]["customer_email"] == "n@example.test"


def test_execution_export_leaves_out_payloads(api, test_db):
    test_db.ai_executions.insert_one(
        {
            "execution_id": "exec_1",
            "ticket_id": "SK-1001",
            "provider": "jev",
            "status": "Succeeded",
            "request_payload_redacted": {"note": "payload-marker"},
            "usage": {"input_tokens": 120, "output_tokens": 12},
            "normalized_result": {"category": "Returns & Refunds"},
        }
    )

    response = api.get("/api/exports/executions.csv")
    rows = read_csv(response)

    assert rows[0]["input_tokens"] == "120"
    assert rows[0]["category"] == "Returns & Refunds"
    assert "payload-marker" not in response.text


def test_comparison_export_has_per_field_columns(api, test_db):
    test_db.comparisons.insert_one(
        {
            "comparison_id": "cmp_1",
            "ticket_id": "SK-1001",
            "status": "Completed",
            "field_comparison": {"priority": {"jev": "Medium", "gpt": "High", "match": False}},
            "agreement_rate": 0.8,
        }
    )

    rows = read_csv(api.get("/api/exports/comparisons.csv"))

    assert (rows[0]["priority_jev"], rows[0]["priority_gpt"], rows[0]["priority_match"]) == (
        "Medium",
        "High",
        "false",
    )


def test_unknown_export_is_404(api):
    assert api.get("/api/exports/secrets.csv").status_code in (404, 422)
