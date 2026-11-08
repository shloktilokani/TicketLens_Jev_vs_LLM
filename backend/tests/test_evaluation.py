import csv
import io
import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.taxonomy import SUBCATEGORIES
from app.main import create_app
from app.services.evaluation import compute, macro_f1
from app.services.run_report import accuracy_section

CONTEXT = Path(__file__).parents[2] / ".context"
V1 = CONTEXT / "sample_tickets_100.csv"
V2 = CONTEXT / "sample_tickets_100_v2.csv"
LABELS = [
    "expected_category",
    "expected_subcategory",
    "expected_priority",
    "expected_sentiment",
    "expected_escalation_required",
]
ANSWER = {
    "category": "Returns & Refunds",
    "subcategory": "Refund Delay",
    "priority": "Medium",
    "sentiment": "Negative",
    "escalation_required": False,
}
ROMANISED_HINDI = re.compile(
    r"\b(hai|hain|nahi|kya|mera|mujhe|kar|ka|ki|ke|bhi|abhi|aur|par|chahiye)\b", re.IGNORECASE
)


def rows(path: Path) -> list[dict]:
    return list(csv.DictReader(io.StringIO(path.read_text(encoding="utf-8-sig"))))


# --- the corrected dataset ------------------------------------------------------------------


def test_v2_keeps_every_label_in_order():
    supplied, corrected = rows(V1), rows(V2)

    assert len(corrected) == 100
    for old, new in zip(supplied, corrected, strict=True):
        assert [new[k] for k in LABELS] == [old[k] for k in LABELS]


def test_v2_titles_no_longer_give_away_the_answer():
    subcategories = {s.lower() for subs in SUBCATEGORIES.values() for s in subs}
    for row in rows(V2):
        title = row["title"].lower()
        assert title not in subcategories
        assert row["expected_subcategory"].lower() not in title, row["title"]
        assert row["expected_category"].lower() not in title, row["title"]


def test_v2_titles_are_unique_and_text_is_english():
    data = rows(V2)
    assert len({row["title"] for row in data}) == 100
    for row in data:
        assert not ROMANISED_HINDI.search(row["description"]), row["description"]
        assert not ROMANISED_HINDI.search(row["title"]), row["title"]
        assert row["customer_email"].endswith("@example.test")


def test_v2_covers_all_six_categories_without_severe_imbalance():
    counts = {}
    for row in rows(V2):
        counts[row["expected_category"]] = counts.get(row["expected_category"], 0) + 1
    assert len(counts) == 6
    assert min(counts.values()) >= 10


def test_v2_passes_the_real_import_checks(api):
    response = api.post(
        "/api/imports/tickets?dry_run=true",
        content=V2.read_bytes(),
        headers={"Content-Type": "text/csv"},
    )

    summary = response.json()
    assert (summary["total_rows"], summary["imported"], summary["invalid"]) == (100, 100, 0)
    assert all(row["labelled"] for row in summary["preview"])


# --- the maths ------------------------------------------------------------------------------


def run(answer: dict | None, *, status="Succeeded", model="qwen3:8b") -> dict:
    return {"status": status, "normalized_result": answer, "requested_model": model}


def test_macro_f1_matches_a_hand_calculation():
    # a: precision 1, recall 0.5, F1 2/3. b: precision 2/3, recall 1, F1 0.8. Mean 0.7333.
    assert macro_f1(["a", "a", "b", "b"], ["a", "b", "b", "b"]) == pytest.approx(0.73333, abs=1e-4)
    assert macro_f1(["a"], ["b"]) == 0
    assert macro_f1([], []) is None


def test_accuracy_uses_only_scored_runs_and_reports_every_denominator():
    labels = {"SK-1": ANSWER, "SK-2": ANSWER, "SK-3": ANSWER, "SK-4": ANSWER}
    wrong = ANSWER | {"priority": "High"}
    runs = {
        ("SK-1", "jev"): run(ANSWER),
        ("SK-2", "jev"): run(wrong),
        ("SK-3", "jev"): run(None, status="Failed"),
        ("SK-1", "gpt"): run(wrong),
        ("SK-2", "gpt"): run(wrong),
    }

    result = compute(labels, runs)

    jev = result["sides"]["jev"]
    assert (jev["labelled"], jev["scored"], jev["failed"], jev["not_run"]) == (4, 2, 1, 1)
    assert jev["per_field"]["priority"] == {
        "correct": 1,
        "scored": 2,
        "accuracy": 0.5,
        "macro_f1": None,  # too few samples to be meaningful
    }
    assert jev["per_field"]["category"]["accuracy"] == 1
    assert jev["exact_match"] == {"correct": 1, "scored": 2, "accuracy": 0.5}
    assert jev["models"] == ["qwen3:8b"]
    llm = result["sides"]["llm"]
    assert (llm["scored"], llm["not_run"]) == (2, 2)
    assert llm["exact_match"]["correct"] == 0


def test_head_to_head_counts_only_tickets_both_sides_answered():
    labels = {"SK-1": ANSWER, "SK-2": ANSWER, "SK-3": ANSWER, "SK-4": ANSWER, "SK-5": ANSWER}
    wrong = ANSWER | {"sentiment": "Neutral"}
    other = ANSWER | {"sentiment": "Positive"}
    runs = {
        ("SK-1", "jev"): run(ANSWER),
        ("SK-1", "gpt"): run(ANSWER),
        ("SK-2", "jev"): run(ANSWER),
        ("SK-2", "gpt"): run(wrong),
        ("SK-3", "jev"): run(wrong),
        ("SK-3", "gpt"): run(ANSWER),
        ("SK-4", "jev"): run(wrong),
        ("SK-4", "gpt"): run(other),
        ("SK-5", "jev"): run(ANSWER),
    }

    field = compute(labels, runs)["head_to_head"]["per_field"]["sentiment"]

    assert field == {
        "compared": 4,
        "both_correct": 1,
        "jev_only": 1,
        "llm_only": 1,
        "both_wrong": 1,
        "agreed": 1,
        "agreement": 0.25,
    }


def test_confusion_matrix_rows_are_expected_and_columns_are_predicted():
    labels = {"SK-1": ANSWER, "SK-2": ANSWER | {"priority": "Critical"}}
    runs = {
        ("SK-1", "jev"): run(ANSWER | {"priority": "Critical"}),
        ("SK-2", "jev"): run(ANSWER | {"priority": "Critical"}),
    }

    matrix = compute(labels, runs)["sides"]["jev"]["confusion"]["priority"]

    critical, medium = matrix["labels"].index("Critical"), matrix["labels"].index("Medium")
    assert matrix["counts"][medium][critical] == 1  # expected Medium, predicted Critical
    assert matrix["counts"][critical][critical] == 1
    assert sum(map(sum, matrix["counts"])) == 2


def test_escalation_is_labelled_in_words_in_the_matrix():
    runs = {("SK-1", "jev"): run(ANSWER)}

    matrix = compute({"SK-1": ANSWER}, runs)["sides"]["jev"]["confusion"]["escalation_required"]

    assert matrix["labels"] == ["Required", "Not required"]
    assert matrix["counts"][1][1] == 1


def test_macro_f1_appears_once_there_are_enough_samples():
    labels = {f"SK-{i}": ANSWER for i in range(30)}
    runs = {(ticket, "jev"): run(ANSWER) for ticket in labels}

    assert compute(labels, runs)["sides"]["jev"]["per_field"]["category"]["macro_f1"] == 1


def test_results_are_reproducible():
    labels = {"SK-1": ANSWER, "SK-2": ANSWER}
    runs = {("SK-1", "jev"): run(ANSWER), ("SK-2", "gpt"): run(ANSWER)}

    assert compute(labels, runs) == compute(dict(labels), dict(runs))


def test_report_section_shows_scores_with_denominators():
    labels = {"SK-1": ANSWER, "SK-2": ANSWER}
    runs = {
        ("SK-1", "jev"): run(ANSWER),
        ("SK-2", "jev"): run(ANSWER | {"priority": "High"}),
        ("SK-1", "gpt"): run(None, status="Failed"),
    }

    html = accuracy_section(compute(labels, runs))

    assert "Accuracy against labelled answers" in html
    assert "50% (1/2)" in html
    assert "LLM 1 failed" in html


# --- end to end -----------------------------------------------------------------------------


@pytest.fixture
def api(test_settings, test_db):
    settings = test_settings.model_copy(update={"mock_providers": True, "mock_delay_seconds": 0})
    with TestClient(create_app(settings)) as client:
        yield client


def import_labelled(api, count: int = 2) -> list[str]:
    selected = rows(V2)[:count]
    out = io.StringIO()
    writer = csv.DictWriter(out, list(selected[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(selected)
    response = api.post(
        "/api/imports/tickets",
        content=out.getvalue().encode(),
        headers={"Content-Type": "text/csv"},
    )
    assert response.status_code == 200, response.text
    return response.json()["imported_ticket_ids"]


def test_no_labels_is_an_empty_state_not_zero_percent(api):
    assert api.get("/api/evaluation").json() == {"labelled_tickets": 0, "scored": False}


def test_fake_runs_are_never_scored(api):
    ticket_id = import_labelled(api, 1)[0]
    api.post(f"/api/tickets/{ticket_id}/runs/jev")

    result = api.get("/api/evaluation").json()

    assert result["labelled_tickets"] == 1
    assert result["scored"] is False


def test_real_runs_are_scored_using_the_latest_finished_attempt(api, test_db):
    ticket_id = import_labelled(api, 1)[0]
    for _ in range(2):
        api.post(f"/api/tickets/{ticket_id}/runs/jev")
    test_db.ai_executions.update_many({}, {"$set": {"requested_model": "autotrust-jev:9b"}})
    newest = test_db.ai_executions.find_one(sort=[("started_at", -1), ("_id", -1)])
    test_db.ai_executions.update_one(
        {"_id": newest["_id"]}, {"$set": {"status": "Failed", "normalized_result": None}}
    )

    jev = api.get("/api/evaluation").json()["sides"]["jev"]

    assert (jev["scored"], jev["failed"]) == (0, 1)


def test_labels_never_reach_a_model(api):
    ticket_id = import_labelled(api, 1)[0]

    execution = api.post(f"/api/tickets/{ticket_id}/runs/gpt").json()

    sent = str([execution["input_snapshot"], execution["request_payload_redacted"]])
    assert "expected" not in sent
    assert "evaluation_label" not in sent
    assert "shopkart-synthetic" not in sent


def test_the_dataset_downloads_and_does_not_seed_the_database(api, test_db):
    response = api.get("/api/imports/sample-dataset")

    assert response.status_code == 200
    assert "attachment" in response.headers["content-disposition"]
    assert response.text.lstrip("﻿").startswith("title,description")
    assert len(list(csv.DictReader(io.StringIO(response.text.lstrip("﻿"))))) == 100
    assert test_db.tickets.count_documents({}) == 0
