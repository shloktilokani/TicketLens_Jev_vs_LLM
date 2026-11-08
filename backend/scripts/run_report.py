"""Write the HTML report for one test run.

Run from backend/:
    .venv/bin/python -m scripts.run_report --run-id 2026-11-07-local --name "Local Models Run" \\
        --note "..." --comparisons cmp_a,cmp_b,...

Writes reports/test-runs/<run-id>.html and <run-id>.json (the run's comparison IDs and labels),
so a report can be regenerated later from the same records.
"""

import argparse
import json
import sys
from pathlib import Path

from app.core.clock import utc_now
from app.core.settings import get_settings
from app.repositories.database import connect, find_in
from app.services.dashboard import load_rows
from app.services.evaluation import summary
from app.services.run_metrics import compute
from app.services.run_report import render

REPORTS = Path(__file__).resolve().parents[2] / "reports" / "test-runs"


def load_run(db, comparison_ids: list[str]) -> list[dict]:
    docs = {
        c["comparison_id"]: c for c in find_in(db, "comparisons", "comparison_id", comparison_ids)
    }
    missing = [c for c in comparison_ids if c not in docs]
    if missing:
        sys.exit(f"Comparison(s) not found: {', '.join(missing)}")
    return load_rows(db, [docs[c] for c in comparison_ids])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--note", default="")
    parser.add_argument("--comparisons", required=True, help="comma-separated comparison IDs")
    args = parser.parse_args()

    ids = [c.strip() for c in args.comparisons.split(",") if c.strip()]
    settings = get_settings()
    client = connect(settings)
    try:
        db = client[settings.mongodb_database]
        rows = load_run(db, ids)
        evaluation = summary(db)
    finally:
        client.close()

    first = rows[0]

    def model(side: str) -> str:
        execution = first[side] or {}
        return execution.get("actual_model") or execution.get("requested_model", "—")

    meta = {
        "run_id": args.run_id,
        "name": args.name,
        "created_at": utc_now().isoformat(),
        "jev_label": model("jev"),
        "llm_label": model("llm"),
        "note": args.note,
    }
    REPORTS.mkdir(parents=True, exist_ok=True)
    html_path = REPORTS / f"{args.run_id}.html"
    html_path.write_text(
        render(meta, compute(rows), rows, evaluation if evaluation["scored"] else None),
        encoding="utf-8",
    )
    (REPORTS / f"{args.run_id}.json").write_text(
        json.dumps(meta | {"comparisons": ids}, indent=2) + "\n"
    )
    print(html_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
