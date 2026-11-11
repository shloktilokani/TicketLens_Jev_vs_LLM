# reports/

Saved reports of test runs: Jev versus the LLM on a set of tickets. Each report is a dated snapshot, not a live view, so it is never updated after the run.

## Files

| Path | Purpose |
|---|---|
| `test-runs/<run-id>.html` | The report: agreement and Cohen's kappa per field, time, reliability, tokens and cost, Jev confidence, label distributions, disagreements and every ticket. Runs with labelled tickets also show accuracy |
| `test-runs/<run-id>.json` | The run's comparison IDs and labels, so its report can be regenerated |

| Run | What it tested |
|---|---|
| `2026-11-07-run-1-fake-ai` | 10 tickets on the fake AI. Tests the app, not the models |
| `2026-11-08-run-2-local-models` | 10 tickets on `autotrust-jev:9b` and `qwen3:8b` |
| `2026-11-08-run-3-labelled-100` | The 100 labelled tickets on the same models, scored for accuracy. Run on the isolated `ticketlens_e2e` database; preliminary until the dataset is reviewed |

## Make a report

From `backend/`:

```bash
.venv/bin/python -m scripts.run_report --run-id <id> --name "<name>" --note "<note>" --comparisons <cmp_a,cmp_b,...>
```

Set `MONGODB_DATABASE` to read from another database, such as `ticketlens_e2e`.

## Gotchas

- **Agreement is not accuracy.** Accuracy appears only when the tickets have labels.
- **Reports load fonts from Google Fonts** when opened in a browser.
