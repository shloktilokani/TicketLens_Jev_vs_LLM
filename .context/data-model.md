# MongoDB Data Model

Database name: `ticketlens`

Use BSON ObjectId for internal `_id` values and UTC BSON Date values for timestamps. Store human-readable ticket IDs separately.

## 1. `tickets`

Example document:

```json
{
  "_id": "ObjectId",
  "ticket_id": "SK-1001",
  "title": "Refund not received for returned headphones",
  "description": "I returned my headphones last week but the refund has not arrived.",
  "customer": {
    "name": "Aarav Mehta",
    "email": "aarav@example.test"
  },
  "order": {
    "order_id": "ORD-2026-10001",
    "product_name": "Wireless Headphones"
  },
  "submission_channel": "Website",
  "status": "Open",
  "final_classification": {
    "category": "Returns & Refunds",
    "subcategory": "Refund Delay",
    "priority": "Medium",
    "sentiment": "Negative",
    "escalation_required": false,
    "selected_from_execution_id": null,
    "manually_edited": false,
    "updated_at": null
  },
  "operator_notes": [],
  "source": {
    "type": "manual",
    "import_batch_id": null,
    "source_fingerprint": "sha256..."
  },
  "is_sample": false,
  "taxonomy_version": "1.0",
  "created_at": "BSON Date",
  "updated_at": "BSON Date"
}
```

Notes:
- `final_classification` is null until the operator selects/edits a final result.
- Do not store sample ground truth in fields returned to AI providers.
- Sample evaluation labels should be stored separately in `evaluation_labels`, or in a clearly isolated protected field that is never included in provider input. Prefer a separate `evaluation_labels` collection.

## 2. `evaluation_labels`

One record per labelled sample ticket:

```json
{
  "_id": "ObjectId",
  "ticket_id": "SK-1001",
  "taxonomy_version": "1.0",
  "expected": {
    "category": "Returns & Refunds",
    "subcategory": "Refund Delay",
    "priority": "Medium",
    "sentiment": "Negative",
    "escalation_required": false
  },
  "dataset_version": "shopkart-synthetic-v1",
  "created_at": "BSON Date"
}
```

This collection must never be read by provider request-building code. It is only for evaluation after model results are stored.

## 3. `ai_executions`

One document for every provider attempt, including failures:

```json
{
  "_id": "ObjectId",
  "execution_id": "exec_<uuid>",
  "ticket_id": "SK-1001",
  "comparison_id": "cmp_<uuid>",
  "provider": "jev",
  "requested_model": "jev-latest",
  "actual_model": "jev-1.x",
  "status": "Succeeded",
  "started_at": "BSON Date",
  "completed_at": "BSON Date",
  "duration_ms": 245,
  "input_snapshot": {
    "title": "Refund not received",
    "description": "Original ticket text...",
    "customer_context": {},
    "taxonomy_version": "1.0"
  },
  "request_payload_redacted": {},
  "response_payload_redacted": {},
  "normalized_result": {
    "category": "Returns & Refunds",
    "subcategory": "Refund Delay",
    "priority": "Medium",
    "sentiment": "Negative",
    "escalation_required": false,
    "confidence": {
      "category": 0.91,
      "subcategory": 0.84
    },
    "summary": null,
    "suggested_resolution": null,
    "unsupported_fields": ["summary", "suggested_resolution"]
  },
  "usage": {
    "input_tokens": 120,
    "output_tokens": 12,
    "total_tokens": 132,
    "usage_source": "provider_reported"
  },
  "pricing_snapshot": {
    "currency": "USD",
    "input_per_million": 0.042,
    "output_per_million": 0,
    "pricing_version": "jev-default-2026-11"
  },
  "estimated_cost": {
    "amount": 0.00000504,
    "currency": "USD",
    "is_estimate": true
  },
  "error": null,
  "prompt_version": "1.0",
  "taxonomy_version": "1.0",
  "created_at": "BSON Date"
}
```

Important:
- Never persist API keys, Authorization headers, cookies, or secret environment values.
- Persist complete request/response payloads after redacting credentials and irrelevant transport headers.
- For failed calls, store whatever is known: start time, provider, model, safe request snapshot, status, duration, error code/message. Usage may be null.
- Use Decimal128 or integer micro-units for financial amounts to avoid floating-point accumulation errors. Preserve original rate snapshot.
- Token counts may be null if provider does not return usage.

## 4. `comparisons`

```json
{
  "_id": "ObjectId",
  "comparison_id": "cmp_<uuid>",
  "ticket_id": "SK-1001",
  "jev_execution_id": "exec_<uuid>",
  "gpt_execution_id": "exec_<uuid>",
  "status": "Completed",
  "field_comparison": {
    "category": {"jev": "Returns & Refunds", "gpt": "Returns & Refunds", "match": true},
    "subcategory": {"jev": "Refund Delay", "gpt": "Refund Delay", "match": true},
    "priority": {"jev": "Medium", "gpt": "High", "match": false},
    "sentiment": {"jev": "Negative", "gpt": "Negative", "match": true},
    "escalation_required": {"jev": false, "gpt": false, "match": true}
  },
  "agreement_count": 4,
  "comparable_field_count": 5,
  "agreement_rate": 0.8,
  "created_at": "BSON Date"
}
```

Statuses: `Completed`, `Partial`, `Unavailable`.

Only compare fields both providers support. Never compare summary/resolution for Jev.

## 5. `bulk_jobs`

Persist job progress for bulk execution:

- `job_id`
- selected ticket IDs or selection mode
- providers requested
- status: `Queued`, `Running`, `Completed`, `Completed With Errors`, `Interrupted`, `Failed`
- total, completed, failed, skipped counts
- per-ticket/provider outcomes
- created/started/completed timestamps
- safe error summary

Do not store credentials.

## 6. `app_settings`

Use one active settings document initially:
- active GPT model
- Jev model alias
- prompt templates and prompt version
- taxonomy and taxonomy version
- pricing table by provider/model
- bulk concurrency limit
- updated timestamp

API keys are not stored here. They remain in backend environment variables.

## 7. `counters`

Use an atomic counter for sequential ticket IDs:

```json
{
  "_id": "ticket_id",
  "sequence": 1000
}
```

Use `find_one_and_update` with `$inc` and `ReturnDocument.AFTER` to allocate the next number. Format as `SK-{sequence}`. Handle first-time counter initialization safely.

## 8. Required indexes

Create indexes at application startup or through an explicit initialization command:
- `tickets.ticket_id`: unique
- `tickets.created_at`: descending
- `tickets.status`
- `tickets.final_classification.category`
- `tickets.source.source_fingerprint`: unique sparse/partial where suitable
- `ai_executions.execution_id`: unique
- `ai_executions.ticket_id + started_at`
- `ai_executions.provider + started_at`
- `comparisons.comparison_id`: unique
- `comparisons.ticket_id + created_at`
- `evaluation_labels.ticket_id`: unique
- `bulk_jobs.job_id`: unique

Avoid unique indexes on nullable values unless a partial filter is used.

## 9. Deletion behavior

When deleting a ticket:
1. Confirm operator intent in UI.
2. Delete comparisons referencing the ticket.
3. Delete AI execution records for the ticket.
4. Delete evaluation labels for the ticket if it is a sample ticket.
5. Delete the ticket document last.
6. If any dependent deletion fails, stop and keep the ticket; return a clear error.
7. Make repeated delete attempts safe.

Do not assume MongoDB transactions are enabled on a standalone local Community Edition server.
