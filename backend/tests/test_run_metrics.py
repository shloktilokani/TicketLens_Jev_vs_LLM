import pytest

from app.services.run_metrics import FIELDS, compute, kappa, percentile


def execution(ms, result=None, status="Succeeded", tokens=None):
    usage = (
        {"input_tokens": tokens[0], "output_tokens": tokens[1], "usage_source": "provider_reported"}
        if tokens
        else {"usage_source": "unavailable"}
    )
    return {"status": status, "duration_ms": ms, "normalized_result": result, "usage": usage}


def result(category="Returns & Refunds", priority="Medium", conf=0.9, summary=None):
    return {
        "category": category,
        "subcategory": "Refund Delay",
        "priority": priority,
        "sentiment": "Negative",
        "escalation_required": False,
        "confidence": {"category": conf, "priority": conf},
        "summary": summary,
    }


def comparison(jev, llm):
    if jev and llm:
        fields = {f: {"jev": jev[f], "gpt": llm[f], "match": jev[f] == llm[f]} for f in FIELDS}
        agreed = sum(v["match"] for v in fields.values())
        return {
            "status": "Completed",
            "field_comparison": fields,
            "agreement_count": agreed,
            "agreement_rate": agreed / 5,
        }
    return {
        "status": "Partial",
        "field_comparison": {},
        "agreement_count": 0,
        "agreement_rate": None,
    }


def row(n, jev, llm):
    jr, lr = (jev or {}).get("normalized_result"), (llm or {}).get("normalized_result")
    return {
        "ticket": {"ticket_id": f"SK-{n}", "title": f"T{n}"},
        "jev": jev,
        "llm": llm,
        "comparison": comparison(jr, lr),
    }


ROWS = [
    row(
        1,
        execution(1000, result(conf=0.9)),
        execution(3000, result(summary="Refund late."), tokens=(700, 60)),
    ),
    row(
        2,
        execution(2000, result(priority="High", conf=0.6)),
        execution(5000, result(summary="Two words here."), tokens=(800, 40)),
    ),
    row(3, execution(1500, result(category="Product Issues", conf=0.5)), None),
]


def test_percentile_and_kappa():
    assert percentile([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 90) == 9
    assert percentile([], 90) is None
    assert kappa([("a", "a"), ("b", "b")]) == 1.0
    assert kappa([("a", "a"), ("a", "a")]) is None  # no variety: chance agreement is 100%
    assert kappa([("a", "b"), ("b", "a")]) == pytest.approx(-1.0)


def test_agreement_metrics_use_completed_comparisons_only():
    m = compute(ROWS)

    assert m["tickets"] == 3
    assert m["comparisons"] == {"Completed": 2, "Partial": 1}
    assert m["exact_matches"] == 1
    assert m["per_field"]["priority"] == {"agreed": 1, "compared": 2, "rate": 0.5, "kappa": 0.0}
    assert m["per_field"]["category"]["rate"] == 1.0
    assert m["mean_agreement"] == pytest.approx(0.9)
    assert m["disagreements"] == [
        {"ticket_id": "SK-2", "title": "T2", "field": "priority", "jev": "High", "llm": "Medium"}
    ]


def test_latency_tokens_and_outcomes():
    m = compute(ROWS)

    assert m["latency"]["jev"]["median"] == 1500
    assert m["latency"]["llm"]["mean"] == 4000
    assert (
        m["wall_clock"]["max"] == 5000
    )  # Jev and LLM run in parallel: the slower one sets the pace
    assert m["tokens"]["llm"]["input"] == 1500 and m["tokens"]["llm"]["output"] == 100
    assert m["tokens"]["llm"]["output_per_second"] == pytest.approx((60 / 3 + 40 / 5) / 2)
    assert m["tokens"]["jev"]["reported_runs"] == 0
    assert m["outcomes"]["llm"]["total"] == 2
    assert m["cost"]["jev"]["total"] is None


def test_jev_confidence_split_by_agreement():
    conf = compute(ROWS)["jev_confidence"]["priority"]

    assert conf["when_agree"] == 0.9 and conf["when_differ"] == 0.6
