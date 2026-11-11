"""Metrics for one test run: Jev vs LLM over a set of comparisons.

Agreement is not accuracy: these numbers compare the two providers with each other. Accuracy needs
human-verified labels (evaluation_labels) and is reported only when they exist.
"""

import math
from collections import Counter
from statistics import mean, median

FIELDS = ["category", "subcategory", "priority", "sentiment", "escalation_required"]
SIDES = ("jev", "llm")


def percentile(values: list[float], pct: float) -> float | None:
    """Nearest-rank percentile; None for an empty list."""
    if not values:
        return None
    ranked = sorted(values)
    return ranked[max(0, math.ceil(pct / 100 * len(ranked)) - 1)]


def kappa(pairs: list[tuple]) -> float | None:
    """Cohen's kappa: agreement corrected for chance. None if undefined (no pairs or no variety)."""
    if not pairs:
        return None
    n = len(pairs)
    observed = sum(a == b for a, b in pairs) / n
    left, right = Counter(a for a, _ in pairs), Counter(b for _, b in pairs)
    expected = sum(left[k] * right[k] for k in left) / (n * n)
    return None if expected == 1 else (observed - expected) / (1 - expected)


def latency(executions: list[dict]) -> dict:
    ms = [e["duration_ms"] for e in executions if e.get("duration_ms") is not None]
    return {
        "count": len(ms),
        "mean": mean(ms) if ms else None,
        "median": median(ms) if ms else None,
        "p90": percentile(ms, 90),
        "min": min(ms, default=None),
        "max": max(ms, default=None),
    }


def tokens(executions: list[dict]) -> dict:
    usage = [e.get("usage") or {} for e in executions]
    reported = [u for u in usage if u.get("usage_source") == "provider_reported"]
    total_in = sum(u.get("input_tokens") or 0 for u in reported)
    total_out = sum(u.get("output_tokens") or 0 for u in reported)
    rates = [
        (e["usage"]["output_tokens"] or 0) / (e["duration_ms"] / 1000)
        for e in executions
        if (e.get("usage") or {}).get("usage_source") == "provider_reported"
        and e.get("duration_ms")
    ]
    return {
        "reported_runs": len(reported),
        "input": total_in if reported else None,
        "output": total_out if reported else None,
        "mean_input": total_in / len(reported) if reported else None,
        "mean_output": total_out / len(reported) if reported else None,
        "output_per_second": mean(rates) if rates else None,
    }


def outcomes(executions: list[dict]) -> dict:
    counts = Counter(e["status"] for e in executions)
    total = len(executions)
    return {
        "total": total,
        "counts": dict(counts),
        "success_rate": counts.get("Succeeded", 0) / total if total else None,
    }


def cost(executions: list[dict]) -> dict:
    amounts = [
        float(e["estimated_cost"]["amount"])
        for e in executions
        if (e.get("estimated_cost") or {}).get("amount") is not None
    ]
    return {"priced_runs": len(amounts), "total": sum(amounts) if amounts else None}


def jev_confidence(rows: list[dict]) -> dict:
    """Jev's own confidence per field, split by whether the LLM agreed."""
    result = {}
    for field in FIELDS:
        agree, differ = [], []
        for row in rows:
            conf = (
                ((row["jev"] or {}).get("normalized_result") or {}).get("confidence", {}).get(field)
            )
            match = (row["comparison"]["field_comparison"].get(field) or {}).get("match")
            if conf is None or match is None:
                continue
            (agree if match else differ).append(conf)
        everything = agree + differ
        result[field] = {
            "mean": mean(everything) if everything else None,
            "when_agree": mean(agree) if agree else None,
            "when_differ": mean(differ) if differ else None,
        }
    return result


def compute(rows: list[dict]) -> dict:
    """`rows`: one dict per ticket with keys ticket, jev, llm (executions or None), comparison."""
    by_side = {side: [r[side] for r in rows if r[side]] for side in SIDES}
    results = {side: [(r[side] or {}).get("normalized_result") for r in rows] for side in SIDES}
    complete = [r for r in rows if r["comparison"]["status"] == "Completed"]

    per_field = {}
    for field in FIELDS:
        pairs = [
            (
                r["comparison"]["field_comparison"][field]["jev"],
                r["comparison"]["field_comparison"][field]["gpt"],
            )
            for r in complete
        ]
        agreed = sum(a == b for a, b in pairs)
        per_field[field] = {
            "agreed": agreed,
            "compared": len(pairs),
            "rate": agreed / len(pairs) if pairs else None,
            "kappa": kappa(pairs),
        }

    distributions = {
        side: {
            field: dict(Counter(res[field] for res in results[side] if res))
            for field in ("category", "priority", "sentiment", "escalation_required")
        }
        for side in SIDES
    }
    summaries = [res["summary"] for res in results["llm"] if res and res.get("summary")]
    disagreements = [
        {
            "ticket_id": r["ticket"]["ticket_id"],
            "title": r["ticket"]["title"],
            "field": f,
            "jev": v["jev"],
            "llm": v["gpt"],
        }
        for r in complete
        for f, v in r["comparison"]["field_comparison"].items()
        if v["match"] is False
    ]
    wall = [
        max(r["jev"]["duration_ms"], r["llm"]["duration_ms"])
        for r in rows
        if r["jev"]
        and r["llm"]
        and r["jev"].get("duration_ms") is not None
        and r["llm"].get("duration_ms") is not None
    ]
    return {
        "tickets": len(rows),
        "comparisons": dict(Counter(r["comparison"]["status"] for r in rows)),
        "exact_matches": sum(
            1 for r in complete if r["comparison"]["agreement_count"] == len(FIELDS)
        ),
        "mean_agreement": mean([r["comparison"]["agreement_rate"] for r in complete])
        if complete
        else None,
        "per_field": per_field,
        "outcomes": {side: outcomes(by_side[side]) for side in SIDES},
        "latency": {side: latency(by_side[side]) for side in SIDES},
        "wall_clock": latency([{"duration_ms": w} for w in wall]),
        "tokens": {side: tokens(by_side[side]) for side in SIDES},
        "cost": {side: cost(by_side[side]) for side in SIDES},
        "jev_confidence": jev_confidence(complete),
        "distributions": distributions,
        "summary_words": mean([len(s.split()) for s in summaries]) if summaries else None,
        "disagreements": disagreements,
    }
