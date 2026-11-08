"""Accuracy against labelled answers (ai-evaluation.md section 9).

Scores each side's latest finished real run per ticket. Failed and missing runs are reported, not
counted as wrong, and fake-provider runs never count. Labels are read here, after model results
are stored, and never by provider request-building code.
"""

from collections import Counter
from statistics import mean

from pymongo.database import Database

from app.core.taxonomy import ExecutionStatus, Priority, Sentiment, active_categories
from app.repositories import executions, labels
from app.services.run_metrics import FIELDS

SIDES = {"jev": "jev", "llm": "gpt"}  # dashboard name -> stored provider key
MIN_SAMPLES_FOR_F1 = 30  # below this, macro-F1 swings too much on a single ticket to be useful
REQUIRED, NOT_REQUIRED = "Required", "Not required"
FIXED_MATRIX_LABELS = {
    "priority": [p.value for p in Priority],
    "sentiment": [s.value for s in Sentiment],
    "escalation_required": [REQUIRED, NOT_REQUIRED],
}


def rate(part: int, whole: int) -> float | None:
    return part / whole if whole else None


def macro_f1(expected: list, predicted: list) -> float | None:
    """The unweighted mean F1 over every class seen on either side. None with no samples."""
    if not expected:
        return None
    hits = Counter(e for e, p in zip(expected, predicted, strict=True) if e == p)
    actual, guessed = Counter(expected), Counter(predicted)
    scores = [2 * hits[c] / (actual[c] + guessed[c]) for c in actual.keys() | guessed.keys()]
    return mean(scores)


def is_scored(run: dict | None) -> bool:
    return bool(run and run["status"] == ExecutionStatus.SUCCEEDED and run["normalized_result"])


def as_label(field: str, value) -> str:
    if field == "escalation_required":
        return REQUIRED if value else NOT_REQUIRED
    return value


def confusion(field: str, pairs: list[tuple]) -> dict:
    """Rows are the expected answer, columns the predicted one."""
    labelled = [(as_label(field, e), as_label(field, p)) for e, p in pairs]
    names = FIXED_MATRIX_LABELS.get(field) or list(active_categories())
    # Older runs can hold a label a later taxonomy no longer offers; keep them in the count.
    names = names + sorted({v for pair in labelled for v in pair} - set(names))
    counts = [[0 for _ in names] for _ in names]
    for row, column in labelled:
        counts[names.index(row)][names.index(column)] += 1
    return {"labels": names, "counts": counts}


def field_score(pairs: list[tuple]) -> dict:
    correct = sum(e == p for e, p in pairs)
    f1 = None
    if len(pairs) >= MIN_SAMPLES_FOR_F1:
        f1 = macro_f1([e for e, _ in pairs], [p for _, p in pairs])
    return {
        "correct": correct,
        "scored": len(pairs),
        "accuracy": rate(correct, len(pairs)),
        "macro_f1": f1,
    }


def side_summary(label_map: dict, runs: dict, provider: str) -> dict:
    attempts = {t: runs.get((t, provider)) for t in label_map}
    scored = {t: run["normalized_result"] for t, run in attempts.items() if is_scored(run)}
    pairs = {f: [(label_map[t][f], answer[f]) for t, answer in scored.items()] for f in FIELDS}
    exact = sum(all(label_map[t][f] == answer[f] for f in FIELDS) for t, answer in scored.items())
    return {
        "labelled": len(label_map),
        "scored": len(scored),
        "failed": sum(1 for run in attempts.values() if run and not is_scored(run)),
        "not_run": sum(1 for run in attempts.values() if run is None),
        "models": sorted({run["requested_model"] for run in attempts.values() if run}),
        "per_field": {f: field_score(pairs[f]) for f in FIELDS},
        "exact_match": {
            "correct": exact,
            "scored": len(scored),
            "accuracy": rate(exact, len(scored)),
        },
        "confusion": {f: confusion(f, pairs[f]) for f in ("category", *FIXED_MATRIX_LABELS)},
    }


def head_to_head_field(triples: list[tuple]) -> dict:
    """(expected, Jev, LLM) for tickets both sides answered."""
    jev_right = [j == e for e, j, _ in triples]
    llm_right = [g == e for e, _, g in triples]
    both = list(zip(jev_right, llm_right, strict=True))
    agreed = sum(j == g for _, j, g in triples)
    return {
        "compared": len(triples),
        "both_correct": both.count((True, True)),
        "jev_only": both.count((True, False)),
        "llm_only": both.count((False, True)),
        "both_wrong": both.count((False, False)),
        "agreed": agreed,
        "agreement": rate(agreed, len(triples)),
    }


def compute(label_map: dict, runs: dict) -> dict:
    """`label_map`: {ticket_id: expected}. `runs`: {(ticket_id, provider): latest finished run}."""
    sides = {name: side_summary(label_map, runs, key) for name, key in SIDES.items()}
    shared = [
        ticket
        for ticket in label_map
        if is_scored(runs.get((ticket, "jev"))) and is_scored(runs.get((ticket, "gpt")))
    ]
    per_field = {
        field: head_to_head_field(
            [
                (
                    label_map[t][field],
                    runs[(t, "jev")]["normalized_result"][field],
                    runs[(t, "gpt")]["normalized_result"][field],
                )
                for t in shared
            ]
        )
        for field in FIELDS
    }
    return {
        "labelled_tickets": len(label_map),
        "scored": any(side["scored"] for side in sides.values()),
        "sides": sides,
        "head_to_head": {"compared_tickets": len(shared), "per_field": per_field},
    }


def summary(db: Database) -> dict:
    label_map = labels.expected_by_ticket(db)
    if not label_map:
        return {"labelled_tickets": 0, "scored": False}
    return compute(label_map, executions.latest_finished_real(db, list(label_map)))
