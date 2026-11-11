"""What the Overview and Comparisons pages show, read from stored runs.

Fake-provider runs are kept out of the metrics so they can never pass for real results.
"""

from pymongo.database import Database

from app.repositories import comparisons, tickets
from app.repositories.database import find_in
from app.services.run_metrics import compute


def load_rows(db: Database, docs: list[dict]) -> list[dict]:
    """Join comparison records with their two runs and ticket, keeping the given order."""
    run_ids = [i for c in docs for i in (c.get("jev_execution_id"), c.get("gpt_execution_id")) if i]
    runs = {e["execution_id"]: e for e in find_in(db, "ai_executions", "execution_id", run_ids)}
    found = find_in(db, "tickets", "ticket_id", [c["ticket_id"] for c in docs])
    by_id = {t["ticket_id"]: t for t in found}
    return [
        {
            "ticket": by_id.get(
                c["ticket_id"], {"ticket_id": c["ticket_id"], "title": "(deleted)"}
            ),
            "jev": runs.get(c.get("jev_execution_id")),
            "llm": runs.get(c.get("gpt_execution_id")),
            "comparison": c,
        }
        for c in docs
    ]


def is_fake(row: dict) -> bool:
    return any(
        (row[side] or {}).get("requested_model", "").startswith("mock-") for side in ("jev", "llm")
    )


def model_of(execution: dict | None) -> str | None:
    if not execution:
        return None
    return execution.get("actual_model") or execution.get("requested_model")


def summary(db: Database) -> dict:
    rows = load_rows(db, comparisons.newest_first(db))
    real = [r for r in rows if not is_fake(r)]
    return {
        "tickets": tickets.counts(db),
        "real_comparisons": len(real),
        "fake_comparisons_excluded": len(rows) - len(real),
        "models": {
            side: sorted({m for r in real if (m := model_of(r[side]))}) for side in ("jev", "llm")
        },
        "metrics": compute(real) if real else None,
    }


def list_item(row: dict) -> dict:
    c = row["comparison"]
    return {
        "comparison_id": c["comparison_id"],
        "ticket_id": c["ticket_id"],
        "title": row["ticket"]["title"],
        "status": c["status"],
        "agreement_count": c["agreement_count"],
        "comparable_field_count": c["comparable_field_count"],
        "jev_model": model_of(row["jev"]),
        "llm_model": model_of(row["llm"]),
        "jev_ms": (row["jev"] or {}).get("duration_ms"),
        "llm_ms": (row["llm"] or {}).get("duration_ms"),
        "fake": is_fake(row),
        "created_at": c["created_at"],
    }


def list_comparisons(db: Database, limit: int, ticket_id: str | None = None) -> dict:
    docs = comparisons.newest_first(db, limit, ticket_id)
    return {
        "items": [list_item(r) for r in load_rows(db, docs)],
        "total": comparisons.count(db, ticket_id),
    }


def detail(db: Database, comparison_id: str) -> dict | None:
    doc = comparisons.get(db, comparison_id)
    return load_rows(db, [doc])[0] if doc else None
