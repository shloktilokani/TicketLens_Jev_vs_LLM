# MongoDB Data Model (as built, 2026-11-11)

- **Database:** `ticketlens`. The test suite uses `ticketlens_test`, and the browser-test stack uses `ticketlens_e2e`. Both are dropped and recreated freely.
- **Timestamps:** UTC BSON dates, from `core/clock.utc_now`.
- **Money:** exact `Decimal128`. The codec in `repositories/database.py` maps Python `Decimal` to `Decimal128`. A plain `MongoClient` without that codec returns `Decimal128` objects.
- **IDs:** MongoDB's own `_id` is never sent to clients. Records are addressed by readable IDs: `SK-1001` for tickets, then `exec_<hex>`, `cmp_<hex>`, `job_<hex>` and `note_<hex>` for the others.
- **Access:** all database access goes through `backend/app/repositories/`.

## 1. `tickets`

```json
{
  "ticket_id": "SK-1001",
  "title": "Refund still missing",
  "description": "Kept exactly as typed",
  "customer": {"name": "Aarav Mehta", "email": "aarav@example.test"},
  "order": {"order_id": "SKORD-26-00001", "product_name": "Wireless Headphones"},
  "submission_channel": "Email | Chat | Phone | Website",
  "status": "Open | In Progress | Resolved | Closed",
  "final_classification": null,
  "operator_notes": [{"note_id": "note_<hex>", "text": "...", "created_at": "date"}],
  "source": {"type": "manual | csv_import", "import_batch_id": null, "source_fingerprint": null},
  "is_sample": false,
  "taxonomy_version": "1.0",
  "created_at": "date",
  "updated_at": "date"
}
```

- **`final_classification`** is null until the operator saves one. Its shape:
  - the five fields: `category`, `subcategory`, `priority`, `sentiment`, `escalation_required`
  - `selected_from_execution_id`: the run it came from, or null if set by hand
  - `manually_edited`: true if set by hand, or if it differs from that run's answer
  - `taxonomy_version` and `updated_at`
- **`is_sample`** is true for rows imported with labels.
- **`source_fingerprint`** is set for imported rows only, and is used to detect duplicates.
- **Not stored:** `latest_run` in API responses is computed from `ai_executions`.

## 2. `ai_executions`

One document per AI attempt, including failures. It is written as `Running` before the call and completed afterwards.

```json
{
  "execution_id": "exec_<hex>",
  "ticket_id": "SK-1001",
  "comparison_id": "cmp_<hex> or null",
  "provider": "jev | gpt",
  "requested_model": "autotrust-jev:9b",
  "actual_model": "autotrust-jev:9b",
  "status": "Running | Succeeded | Failed | Invalid Response | Cancelled | Timed Out",
  "started_at": "date",
  "completed_at": "date",
  "duration_ms": 1200,
  "input_snapshot": {"ticket_id": "...", "title": "...", "description": "...", "order_id": null, "product_name": null,
                     "submission_channel": "...", "language": "English", "taxonomy_version": "1.0",
                     "categories": {}, "priorities": [], "sentiments": [], "instructions": "the prompt text used"},
  "request_payload_redacted": {},
  "response_payload_redacted": {},
  "normalized_result": {"category": "...", "subcategory": "...", "priority": "...", "sentiment": "...",
                        "escalation_required": false, "confidence": {}, "summary": null,
                        "suggested_resolution": null, "unsupported_fields": [], "warnings": []},
  "usage": {"input_tokens": 1087, "output_tokens": 0, "total_tokens": 1087, "usage_source": "provider_reported"},
  "pricing_snapshot": {"currency": "USD", "input_per_million": "0", "output_per_million": "0", "pricing_version": "local-no-charge"},
  "estimated_cost": {"amount": "0", "currency": "USD", "is_estimate": true},
  "error": null,
  "prompt_version": "1.0",
  "taxonomy_version": "1.0",
  "created_at": "date"
}
```

- **`provider`:** `gpt` means the LLM side, whichever model serves it (see `architecture.md` section 3).
- **Payloads:** Jev's request and response are `{"steps": [...]}`, because it asks in two steps. Keys named like credentials are replaced with `[REDACTED]` (`core/redaction.py`).
- **`error`:** `{code, http_status, message}`, where `message` is safe to show. `code` is a failure kind such as `timeout`, `invalid_response`, `not_configured` or `interrupted`.
- **Rates:** `pricing_snapshot` is saved with the run, so later rate changes never alter its cost. The rate versions are:

  | `pricing_version` | Meaning |
  |---|---|
  | `local-no-charge` | Local models; no charge per call |
  | `typesafe-jev-2026-11` | Hosted Jev at its published input rate |
  | `settings-<timestamp>` | Rates saved on the Settings page |

  Both `pricing_snapshot` and `estimated_cost` are null when no rate is known: fake AI, OpenAI, or runs made before cost logging.
- **Status `Cancelled`** is set at startup on runs left `Running` by a restart.

## 3. `comparisons`

```json
{
  "comparison_id": "cmp_<hex>",
  "ticket_id": "SK-1001",
  "jev_execution_id": "exec_<hex>",
  "gpt_execution_id": "exec_<hex>",
  "status": "Completed | Partial | Unavailable",
  "field_comparison": {"category": {"jev": "...", "gpt": "...", "match": true}},
  "agreement_count": 4,
  "comparable_field_count": 5,
  "agreement_rate": 0.8,
  "created_at": "date"
}
```

- **Fields compared:** only the five shared ones. `match` is null unless both sides have a validated answer.
- **Linking:** both runs get the comparison's `comparison_id`.

## 4. `evaluation_labels`

```json
{
  "ticket_id": "SK-1001",
  "taxonomy_version": "1.0",
  "expected": {"category": "...", "subcategory": "...", "priority": "...", "sentiment": "...", "escalation_required": false},
  "dataset_version": "shopkart-synthetic-v1",
  "created_at": "date"
}
```

- **Origin:** written only by a CSV import of rows that carry `expected_*` columns.
- **Readers:** only `services/evaluation.py`, after runs are stored. Provider input never reads it.

## 5. `bulk_jobs`

```json
{
  "job_id": "job_<hex>",
  "ticket_ids": ["SK-1001"],
  "all_eligible": false,
  "providers": ["jev", "gpt"],
  "status": "Queued | Running | Completed | Completed With Errors | Interrupted | Failed",
  "total": 2, "completed": 2, "failed": 0, "skipped": 0,
  "outcomes": [{"ticket_id": "SK-1001", "provider": "jev", "status": "Succeeded | ... | Skipped", "execution_id": "exec_<hex> or null"}],
  "created_at": "date", "started_at": "date", "completed_at": "date",
  "error_summary": null
}
```

- **`ticket_ids`:** the tickets resolved when the job was created. For an all-eligible job these are the Open and In Progress tickets.
- **Counts:** `total` is tickets × sides.
- **Deletion:** a deleted ticket does not remove its job records; they are history.

## 6. `app_settings`

Settings saved from the Settings page, in one document with `_id: "active"`. Every field is optional, and a missing field falls back to the environment default.

```json
{
  "_id": "active",
  "jev_model": "autotrust-jev:9b",
  "llm_model": "qwen3:8b",
  "jev_escalation_threshold": 0.5,
  "bulk_concurrency": 2,
  "prompt": {"version": "1.1", "instructions": "...", "created_at": "date"},
  "prompt_history": [{"version": "1.0", "instructions": "...", "created_at": "date"}],
  "taxonomy": {"version": "1.1", "categories": {"Orders & Delivery": ["Order Status"]}, "created_at": "date"},
  "taxonomy_history": [],
  "pricing": [{"provider": "gpt", "model": "qwen3:8b", "input_per_million": "1.25", "output_per_million": "2.5", "pricing_version": "settings-..."}],
  "updated_at": "date"
}
```

- **`llm_model`** fills `OLLAMA_MODEL`, or `OPENAI_MODEL` when `LLM_BACKEND=openai`.
- **No secrets:** API keys and connection details are never stored here, and the update API refuses unknown fields.

## 7. `counters`

A single document, `{"_id": "ticket_id", "issued": 23}`. `next_ticket_id` increments it atomically with `$inc` and `upsert`, and formats the result as `SK-{1000 + issued}`. IDs are never reused, but a failed insert can leave a gap.

## 8. Indexes

The indexes are created at startup and by `python -m scripts.init_db`. Both are safe to repeat.

| Collection | Index |
|---|---|
| `tickets` | `ticket_id` unique; `created_at` descending; `status`; `final_classification.category`; `source.source_fingerprint` unique, partial (string values only) |
| `ai_executions` | `execution_id` unique; `ticket_id` + `started_at` descending; `provider` + `started_at` descending |
| `comparisons` | `comparison_id` unique; `ticket_id` + `created_at` descending |
| `evaluation_labels` | `ticket_id` unique |
| `bulk_jobs` | `job_id` unique |

`app_settings` and `counters` need no extra index, because each holds one document.

## 9. Deleting a ticket

`repositories/tickets.delete_with_dependents`:
1. Delete the ticket's `comparisons`, then its `ai_executions`, then its `evaluation_labels`.
2. Delete the ticket last.

Standalone MongoDB has no multi-document transactions. If a step fails, the ticket remains and a retry finishes the job. Deleting a ticket that does not exist does nothing.
