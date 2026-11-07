"""Render one test run as a self-contained HTML report (inline CSS and SVG, no scripts).

The file is written without <html>/<body> wrappers so the same file works opened from disk and
published as an artifact.
"""

from datetime import datetime
from html import escape

from app.services.run_metrics import FIELDS

LABELS = {
    "category": "Category",
    "subcategory": "Subcategory",
    "priority": "Priority",
    "sentiment": "Sentiment",
    "escalation_required": "Escalation",
}

STYLE = """
<style>
/* Layout: one reading column; numbers first, then charts, then the full tables. */
:root {
  --bg: #f6f7f9; --surface: #ffffff; --ink: #14171c; --ink-2: #4a5160; --ink-3: #737b8c;
  --rule: #dfe3ea; --jev: #2a78d6; --llm: #eb6834; --good: #12784a; --bad: #b42318;
  --font: "IBM Plex Sans", ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif;
  --mono: "IBM Plex Mono", ui-monospace, "SF Mono", Menlo, monospace;
}
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {
  --bg: #121418; --surface: #1a1d22; --ink: #eef0f3; --ink-2: #b9c0cc; --ink-3: #8b93a1;
  --rule: #2c313a; --jev: #3987e5; --llm: #d95926; --good: #4cc38a; --bad: #f97066; color-scheme: dark } }
:root[data-theme="dark"] {
  --bg: #121418; --surface: #1a1d22; --ink: #eef0f3; --ink-2: #b9c0cc; --ink-3: #8b93a1;
  --rule: #2c313a; --jev: #3987e5; --llm: #d95926; --good: #4cc38a; --bad: #f97066; color-scheme: dark }
body { background: var(--bg); color: var(--ink); font: 15px/1.55 var(--font);
  padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px)); }
main { max-width: 960px; margin: 0 auto; padding-block: 32px 64px; display: grid; gap: 40px; }
header { display: grid; gap: 10px; }
.eyebrow { font: 600 12px/1.2 var(--mono); letter-spacing: .08em; text-transform: uppercase; color: var(--ink-3); }
h1 { font-size: 30px; line-height: 1.2; margin: 0; text-wrap: balance; }
h2 { font-size: 19px; margin: 0; text-wrap: balance; }
p { margin: 0; max-width: 68ch; color: var(--ink-2); }
section { display: grid; gap: 14px; min-width: 0; }
.sides { display: flex; flex-wrap: wrap; gap: 8px 20px; font-size: 14px; }
.key { display: inline-flex; align-items: center; gap: 8px; }
.swatch { width: 12px; height: 12px; border-radius: 3px; display: inline-block; }
.note { border-left: 3px solid var(--rule); padding-left: 12px; font-size: 14px; }
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px; }
.stat { background: var(--surface); border: 1px solid var(--rule); border-radius: 8px; padding: 14px 16px; display: grid; gap: 4px; }
.stat b { font: 600 26px/1.1 var(--font); font-variant-numeric: tabular-nums; }
.stat span { font-size: 13px; color: var(--ink-2); }
.scroll { overflow-x: auto; min-width: 0; }
table { border-collapse: collapse; width: 100%; font-size: 14px; font-variant-numeric: tabular-nums; }
th, td { text-align: left; padding: 8px 10px; border-bottom: 1px solid var(--rule); vertical-align: top; }
th { font: 600 12px/1.3 var(--mono); letter-spacing: .04em; text-transform: uppercase; color: var(--ink-3); white-space: nowrap; }
td.num, th.num { text-align: right; }
.mono { font-family: var(--mono); font-size: 13px; }
.yes { color: var(--good); } .no { color: var(--bad); font-weight: 600; }
svg { display: block; }
svg text { fill: var(--ink-2); font: 12px var(--font); }
svg .axis { stroke: var(--rule); }
svg .label { fill: var(--ink); }
footer { font-size: 13px; color: var(--ink-3); display: grid; gap: 6px; }
</style>
"""


def fmt(value, digits: int = 0, suffix: str = "") -> str:
    if value is None:
        return "—"
    return f"{value:,.{digits}f}{suffix}"


def pct(value) -> str:
    return "—" if value is None else f"{value * 100:.0f}%"


def secs(ms) -> str:
    return "—" if ms is None else f"{ms / 1000:.2f} s"


def table(headers: list[str], rows: list[list[str]], numeric: set[int] = frozenset()) -> str:
    head = "".join(
        f'<th class="num">{h}</th>' if i in numeric else f"<th>{h}</th>"
        for i, h in enumerate(headers)
    )
    body = "".join(
        "<tr>"
        + "".join(
            f'<td class="num">{c}</td>' if i in numeric else f"<td>{c}</td>"
            for i, c in enumerate(r)
        )
        + "</tr>"
        for r in rows
    )
    return f'<div class="scroll"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'


def agreement_chart(per_field: dict) -> str:
    """Horizontal bars, one per field, 0-100% on one scale."""
    width, left, row = 640, 110, 30
    plot = width - left - 120  # room for the value label
    parts = []
    for i, field in enumerate(FIELDS):
        data = per_field[field]
        y = 10 + i * row
        w = plot * (data["rate"] or 0)
        label = f"{pct(data['rate'])} ({data['agreed']}/{data['compared']})"
        parts.append(
            f'<text x="{left - 10}" y="{y + 13}" text-anchor="end" class="label">{LABELS[field]}</text>'
            f'<rect x="{left}" y="{y + 2}" width="{plot}" height="16" rx="4" fill="var(--rule)" opacity=".45"/>'
            f'<rect x="{left}" y="{y + 2}" width="{max(w, 2):.1f}" height="16" rx="4" fill="var(--ink-2)">'
            f"<title>{LABELS[field]}: {label}</title></rect>"
            f'<text x="{left + plot + 8}" y="{y + 14}">{label}</text>'
        )
    height = 20 + len(FIELDS) * row
    return f'<div class="scroll"><svg viewBox="0 0 {width} {height}" width="{width}" height="{height}" role="img" aria-label="Agreement by field">{"".join(parts)}</svg></div>'


def speed_chart(rows: list[dict]) -> str:
    """Per-ticket dumbbell: Jev and LLM seconds on one shared scale."""
    points = [
        (
            r["ticket"]["ticket_id"],
            (r["jev"] or {}).get("duration_ms"),
            (r["llm"] or {}).get("duration_ms"),
        )
        for r in rows
    ]
    top = max([v for _, a, b in points for v in (a, b) if v is not None] or [1])
    width, left, row = 640, 84, 28
    plot = width - left - 30

    def x(ms: float) -> float:
        return left + plot * ms / top

    parts = []
    for i in range(5):  # faint grid at even steps of the shared scale
        gx = left + plot * i / 4
        parts.append(
            f'<line x1="{gx:.1f}" x2="{gx:.1f}" y1="6" y2="{14 + len(points) * row}" class="axis"/>'
            f'<text x="{gx:.1f}" y="{30 + len(points) * row}" text-anchor="middle">{top * i / 4 / 1000:.1f} s</text>'
        )
    for i, (ticket, jev, llm) in enumerate(points):
        y = 20 + i * row
        parts.append(
            f'<text x="{left - 10}" y="{y + 4}" text-anchor="end" class="label">{escape(ticket)}</text>'
        )
        if jev is not None and llm is not None:
            parts.append(
                f'<line x1="{x(jev):.1f}" x2="{x(llm):.1f}" y1="{y}" y2="{y}" stroke="var(--rule)" stroke-width="2"/>'
            )
        for ms, color, name in ((jev, "var(--jev)", "Jev"), (llm, "var(--llm)", "LLM")):
            if ms is not None:
                parts.append(
                    f'<circle cx="{x(ms):.1f}" cy="{y}" r="5.5" fill="{color}" stroke="var(--surface)" stroke-width="2">'
                    f"<title>{escape(ticket)} · {name}: {secs(ms)}</title></circle>"
                )
    height = 40 + len(points) * row
    return f'<div class="scroll"><svg viewBox="0 0 {width} {height}" width="{width}" height="{height}" role="img" aria-label="Time per ticket">{"".join(parts)}</svg></div>'


def word(value) -> str:
    """Display text for a field value; escalation booleans read as words."""
    if isinstance(value, bool):
        return "Required" if value else "Not required"
    return escape(str(value))


def mark(match) -> str:
    if match is None:
        return '<span class="mono">—</span>'
    return '<span class="yes">✓ Agree</span>' if match else '<span class="no">✗ Differ</span>'


def ticket_rows(rows: list[dict]) -> list[list[str]]:
    out = []
    for r in rows:
        fields = r["comparison"]["field_comparison"]
        jr = (r["jev"] or {}).get("normalized_result") or {}
        lr = (r["llm"] or {}).get("normalized_result") or {}
        cells = []
        for f in ("category", "subcategory", "priority", "sentiment", "escalation_required"):
            j, l_ = jr.get(f, "—"), lr.get(f, "—")
            cells.append(f"{word(j)}<br>{word(l_)}<br>{mark((fields.get(f) or {}).get('match'))}")
        out.append(
            [
                f'<span class="mono">{escape(r["ticket"]["ticket_id"])}</span><br>{escape(r["ticket"]["title"])}'
            ]
            + cells
            + [
                f"{secs((r['jev'] or {}).get('duration_ms'))}<br>{secs((r['llm'] or {}).get('duration_ms'))}"
            ]
        )
    return out


def side(key: str) -> str:
    """Opening of a legend key: a colour swatch for the Jev or LLM series."""
    return f'<span class="key"><span class="swatch" style="background:var(--{key})"></span>'


def render(meta: dict, m: dict, rows: list[dict]) -> str:
    """`meta`: run_id, name, created_at, jev_label, llm_label, note."""
    done = m["comparisons"].get("Completed", 0)
    lat, tok, out, cost = m["latency"], m["tokens"], m["outcomes"], m["cost"]
    stats = [
        (str(m["tickets"]), "tickets run"),
        (f"{done} of {m['tickets']}", "comparisons complete"),
        (f"{m['exact_matches']} of {done}", "agree on all 5 fields"),
        (pct(m["mean_agreement"]), "mean agreement"),
        (secs(lat["jev"]["median"]), "Jev median time"),
        (secs(lat["llm"]["median"]), "LLM median time"),
    ]
    sides = (("jev", "Jev"), ("llm", "LLM"))
    per_field = [
        [LABELS[f], pct(d["rate"]), f"{d['agreed']}/{d['compared']}", fmt(d["kappa"], 2)]
        for f, d in m["per_field"].items()
    ]
    speed = [
        [
            name,
            secs(lat[k]["mean"]),
            secs(lat[k]["median"]),
            secs(lat[k]["p90"]),
            secs(lat[k]["min"]),
            secs(lat[k]["max"]),
        ]
        for k, name in sides
    ] + [
        [
            "Both, side by side",
            *(secs(m["wall_clock"][s]) for s in ("mean", "median", "p90", "min", "max")),
        ]
    ]
    reliability = [
        [
            name,
            str(out[k]["total"]),
            pct(out[k]["success_rate"]),
            ", ".join(f"{s} {n}" for s, n in sorted(out[k]["counts"].items())) or "—",
        ]
        for k, name in sides
    ]
    usage = [
        [
            name,
            fmt(tok[k]["mean_input"]),
            fmt(tok[k]["mean_output"]),
            fmt(tok[k]["input"]),
            fmt(tok[k]["output"]),
            fmt(tok[k]["output_per_second"], 1),
            "Not reported" if not tok[k]["reported_runs"] else f"{tok[k]['reported_runs']} runs",
            "—" if cost[k]["total"] is None else f"${cost[k]['total']:.6f}",
        ]
        for k, name in sides
    ]
    confidence = [
        [LABELS[f], pct(c["mean"]), pct(c["when_agree"]), pct(c["when_differ"])]
        for f, c in m["jev_confidence"].items()
        if c["mean"] is not None
    ]
    dist_rows = []
    for field in ("category", "priority", "sentiment", "escalation_required"):
        values = sorted(
            set(m["distributions"]["jev"][field]) | set(m["distributions"]["llm"][field]), key=str
        )
        for v in values:
            dist_rows.append(
                [
                    LABELS[field],
                    word(v),
                    str(m["distributions"]["jev"][field].get(v, 0)),
                    str(m["distributions"]["llm"][field].get(v, 0)),
                ]
            )
    differ = [
        [
            f'<span class="mono">{escape(d["ticket_id"])}</span>',
            escape(d["title"]),
            LABELS[d["field"]],
            word(d["jev"]),
            word(d["llm"]),
        ]
        for d in m["disagreements"]
    ]
    created = datetime.fromisoformat(meta["created_at"]).strftime("%d %b %Y, %H:%M")
    return f"""<title>{escape(meta["name"])}</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@400;600&display=swap">
{STYLE}
<main>
<header>
  <span class="eyebrow">TicketLens test run · {escape(meta["run_id"])} · {created}</span>
  <h1>{escape(meta["name"])}</h1>
  <div class="sides">{side("jev")}Jev: {escape(meta["jev_label"])}</span>{side("llm")}LLM: {escape(meta["llm_label"])}</span></div>
  <p class="note">{escape(meta["note"])} Agreement shows how often the two sides gave the same answer. It is not accuracy: these tickets have no human-verified answers, so nothing here says which side is right.</p>
</header>
<section aria-label="Summary"><div class="stats">{"".join(f'<div class="stat"><b>{v}</b><span>{label}</span></div>' for v, label in stats)}</div></section>
<section><h2>Agreement by field</h2>
  <p>Share of completed comparisons where Jev and the LLM chose the same value. Kappa corrects for agreement expected by chance (1 = perfect, 0 = chance level, — = undefined because one side always gave the same value).</p>
  {agreement_chart(m["per_field"])}
  {table(["Field", "Agreement", "Agreed / compared", "Kappa"], per_field, {1, 2, 3})}
</section>
<section><h2>Time per ticket</h2>
  <p>Each row is one ticket; the dots show how long each side took. Both run at the same time, so the slower dot sets the wait.</p>
  <div class="sides">{side("jev")}Jev</span>{side("llm")}LLM</span></div>
  {speed_chart(rows)}
  {table(["Side", "Mean", "Median", "90th pct", "Fastest", "Slowest"], speed, {1, 2, 3, 4, 5})}
</section>
<section><h2>Reliability</h2>{table(["Side", "Runs", "Succeeded", "Outcomes"], reliability, {1, 2})}</section>
<section><h2>Tokens and cost</h2>
  <p>Tokens as reported by each provider; never estimated. Local models have no per-call price, and pricing is not configured yet, so cost shows — where nothing was charged or priced.</p>
  {table(["Side", "Mean in", "Mean out", "Total in", "Total out", "Out tokens/s", "Reported", "Cost"], usage, {1, 2, 3, 4, 5})}
  <p>LLM summaries averaged {fmt(m["summary_words"])} words. Jev returns typed decisions only and writes no summaries.</p>
</section>
<section><h2>Jev confidence</h2>
  <p>Jev's own confidence in each answer, overall and split by whether the LLM agreed. It is not comparable with any LLM self-rating.</p>
  {table(["Field", "Mean", "When both agree", "When they differ"], confidence, {1, 2, 3}) if confidence else "<p>No confidence values were returned.</p>"}
</section>
<section><h2>How each side labelled the tickets</h2>{table(["Field", "Value", "Jev", "LLM"], dist_rows, {2, 3})}</section>
<section><h2>Disagreements ({len(differ)})</h2>
  {table(["Ticket", "Title", "Field", "Jev", "LLM"], differ) if differ else "<p>None: the two sides agreed on every compared field.</p>"}
</section>
<section><h2>Every ticket</h2>
  <p>Each cell shows Jev's answer, then the LLM's, then whether they agree.</p>
  {table(["Ticket", "Category", "Subcategory", "Priority", "Sentiment", "Escalation", "Time (Jev / LLM)"], ticket_rows(rows))}
</section>
<footer>
  <span>Generated by backend/scripts/run_report.py from the TicketLens database. Ticket text is synthetic.</span>
  <span>Comparison records: {", ".join(escape(r["comparison"]["comparison_id"]) for r in rows)}</span>
</footer>
</main>
"""
