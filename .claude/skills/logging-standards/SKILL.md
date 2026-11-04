---
name: logging-standards
description: "Ensures meaningful, safe, correctly levelled logging and request tracing without leaking sensitive data. Use whenever code adds or changes logging, error handling, or audit records."
metadata:
  title: "Logging Standards"
  category: "Process & Governance"
  tier: process
  routing: "broad footprint: consider on most non-trivial changes"
  trigger_keywords: "add logging, log statement, error logging, log level, structured logging, sensitive data in logs"
---

## Role Identity

Ensures meaningful, safe, appropriately-leveled logging exists throughout the codebase for production traceability and debugging — logging is treated as a first-class engineering concern, not an afterthought bolted on when something breaks.

## Responsibilities

- Insert or verify log statements at the points that actually matter for debugging a production incident: function/service entry and exit for major operations, every catch/error-handling block, every external call (HTTP, DB, queue, third-party API), and every meaningful state transition (job started/completed/failed, order placed, user authenticated, feature flag flipped).
- Use the idiomatic, already-established logging approach for the detected stack — a real logging library with levels and structured output, not ad hoc `print`/`console.log`, unless raw stdout output is genuinely idiomatic for that context (e.g. a tiny throwaway script or a CLI tool's user-facing output).
- Attach enough context to each log entry (identifiers, operation name, relevant parameters) that a reader can reconstruct what happened without attaching a debugger — but no more than that.
- Ensure error logs capture the actual exception/stack trace, not just a generic "something went wrong" string.
- Verify log levels are used consistently: `debug` for developer-only detail, `info` for normal operational milestones, `warn` for recoverable/unexpected conditions, `error` for failures needing attention. Reject code that logs everything at `info` or everything at `error`.
- Check for and flag missing correlation/trace/request IDs in systems that span multiple services or async boundaries, since without them logs cannot be stitched into a single request's story.
- Confirm that logs are consumable by whatever aggregation platform the org already uses (ELK, Datadog, CloudWatch, Splunk, etc.) — e.g. structured/JSON output where that platform expects it, rather than unparsable free-text.

## Technical Skill Set

- **Node.js/TypeScript**: Winston, Pino, or the framework's built-in logger (e.g. Nest's `Logger`, Fastify's `req.log`); structured JSON transports; child loggers for per-request context.
- **Python**: standard `logging` module with proper handler/formatter config, or `structlog` for structured key-value logs; `logging.exception()` inside `except` blocks to capture tracebacks.
- **Go**: `zap` or `logrus` for structured, leveled logging; `log/slog` (stdlib) as the modern structured default; context-propagated fields for request scoping.
- **Java/Kotlin**: SLF4J as the facade, backed by Logback or Log4j2; MDC (Mapped Diagnostic Context) for correlation IDs across a request thread.
- **Ruby**: the stdlib `Logger` or `SemanticLogger` for structured output in Rails apps.
- **.NET**: `ILogger<T>` / Microsoft.Extensions.Logging, Serilog for structured sinks.
- **Cross-cutting**: log levels (debug/info/warn/error/fatal) and when each is appropriate; correlation IDs / trace IDs (W3C Trace Context, OpenTelemetry spans) for distributed tracing; awareness of log aggregation and APM tooling (ELK stack, Datadog, CloudWatch Logs, Splunk, Grafana Loki) so log shape matches what those systems expect (structured/JSON, consistent field names, timestamps).

## Decision-Making Lens

Every logging decision is a three-way balance:

1. **Traceability/debuggability** — can an engineer reconstruct what happened at 3am from these logs alone, without redeploying with more logging first?
2. **Safety** — does this log line ever risk emitting PII, secrets, API keys, tokens, passwords, or full request/response bodies that might contain sensitive fields?
3. **Signal-to-noise** — does this log line earn its place, or does it just add volume that will bury the log line that actually mattered during an incident, and cost money at the aggregator?

When these are in tension, safety wins over traceability (redact or omit rather than leak), and traceability at `warn`/`error` wins over noise concerns (better to over-log failures than under-log them); `debug`-level verbosity is the release valve for detail that would otherwise be noise in production.

## Trigger Signals

Keywords: `add logging`, `log statement`, `error logging`, `log level`, `structured logging`, `sensitive data in logs` — plus any request to add error handling, wire up an external API/service call, write an async job/background worker/queue consumer, or debug a production issue from logs.

This skill has a **broad trigger footprint, similar to documentation-maintainer**: it should be considered on most non-trivial code-writing tasks, not only when logging is explicitly requested. It is especially relevant whenever a task touches error handling, external API/service calls, retries, or async/background/queue-driven work, since those are exactly the paths that are hardest to debug without adequate logs.

In the orchestrator's 3-signal model (explicit trigger words, task-shape inference, project-context detection), this skill is typically activated by task-shape inference (writing/modifying error handling, integrations, or background jobs) and project-context detection (an existing logging convention in the repo), even when no logging keyword appears in the request. It is **not mutually exclusive** with any persona role also triggered for the same task — it runs alongside, not instead of, roles like backend-developer or devops-engineer.

## Collaboration Behavior

- Runs in parallel alongside almost any persona role that is writing new logic, most commonly **backend-developer**, **devops-engineer**, **SRE**, and **mlops-engineer**, adding or reviewing log statements as that role's code takes shape rather than as a separate pass afterward.
- Defers to the persona role on business logic and architecture; only asserts itself on logging concerns — placement, level, content, and safety of log statements.
- Pushes back when a persona role logs sensitive data (raw request bodies, tokens, passwords, full user records, payment details) — proposes a redacted or field-limited alternative instead of blocking the work outright.
- Pushes back when a persona role over-logs (e.g. logging inside a tight loop at `info`, or logging both the request and every intermediate step at `info`) — proposes collapsing to a single meaningful log line or dropping to `debug`.
- Does not introduce a new logging library or framework when the project already has one in use; adapts to the existing convention even if it would have made a different choice greenfield.

## Output Style / Conventions

- Log levels are used consistently and match the semantic weight described above — no `error`-level logs for expected/handled conditions, no `info`-level logs for unrecoverable failures.
- Log entries are structured (key-value or JSON) wherever the stack's logging library supports it, rather than string-concatenated messages like `"User " + userId + " failed to login"`. Prefer `logger.warn("login_failed", { userId, reason })` -style calls over interpolated strings.
- Every non-obvious log placement gets a brief inline comment or is self-evident from the message text — e.g. why a `debug` log is placed before a retry, or why an `error` log includes a specific field the reader might not expect to need.
- Messages are static/greppable (a fixed message string with structured fields attached), not fully dynamic sentences that make searching logs across occurrences difficult.
- Timestamps, service/module name, and correlation IDs are included via the logger's context mechanism (child logger, MDC, context fields) rather than manually formatted into the message string.

## Anti-Patterns

- Never log secrets, credentials, API keys, tokens, session IDs, or full authentication headers — not even at `debug` level, since debug logs can still ship to aggregators.
- Never log PII (names, emails, phone numbers, addresses, government IDs, payment card data) in plaintext; redact, hash, or omit these fields.
- Never leave debug-only verbose logging (full payload dumps, per-iteration loop logs, raw SQL with bound values) in a production code path without guarding it behind a log-level check or feature flag — it will either flood the aggregator or get silently disabled and become dead weight.
- Never use `print`/`console.log`/`fmt.Println` as a substitute for real structured logging in production code paths — these bypass log levels, structured fields, and aggregator ingestion, and are acceptable only in throwaway scripts, one-off tooling, or genuinely idiomatic CLI user-facing output.
- Never swallow an exception silently or log it as a bare string without the stack trace/exception object — the whole point of an error log is to be actionable later.
- Never log the same event redundantly at multiple layers of the call stack at the same level, producing duplicate noise for a single failure.

## Request Tracing & Investigation Practice

These rules apply to systems that record a run/request history (API backends, pipelines, LLM applications) and to anyone investigating a specific request.

- **One correlation ID per user request, threaded everywhere.** A single run/request ID links the run record, every per-stage or per-call log row, application logs, and any user feedback. Choose a format that encodes useful context and survives same-second collisions (e.g. `<ENV>-<YYYYMMDD>-<HHMMSS>-<short random suffix>`), and keep it stable — downstream queries and foreign keys depend on it.
- **Exactly one run record per user-facing response**, written after the final response is produced, regardless of success or error, inside its own error guard — a logging failure must never hide a valid response. Retries and internal sub-steps must not create duplicate run records.
- **Record skipped stages explicitly** (status `skipped`, reason) rather than omitting rows, so "every run has one row per stage" stays true and queries stay simple.
- **When a stage can run more than once per request**, add a per-call event table (run ID, stage, call index, status, duration, input/output, error detail, token or cost counts). A one-row-per-stage table silently keeps only the last call.
- **Persist decisions the system makes deterministically** (authorisation applied, validation outcome, rejection reason in full) as real columns, so those steps stay auditable — not folded into an opaque JSON blob.
- **Keep a durable secondary write path** (e.g. an append-only JSONL file beside the database write) where losing run history is costly, and don't "clean it up" once the primary is trusted. Catch and log secondary-write failures; never re-raise into the response path.
- **Tag every run with its source** (real user, automated test, parity run, synthetic probe) at write time, so metrics can exclude non-user traffic, and make sure test harnesses actually initialise the logging path — a harness that never opens the log connection produces zero rows while looking fine.
- **Audit outbound notifications (email, webhook, SMS) in their own table** — one row per send attempt outcome (`sent` / `failed` / `rejected` plus a reason code), keyed to the run ID, recording recipients, subject, provider message ID, and error — **never the message body or attachments**. Write it off the response path and never let it raise; it's the only reliable answer to "who did this go to?".
- **Expose per-run summaries through a database view**, not ad-hoc joins — a view that aggregates child tables (stage rows, notification counts, last status) keeps "one run = one row" true for every consumer, where a direct join silently multiplies rows.
- **Requests rejected before your code runs** (framework-level validation errors, auth middleware) produce no run record. Don't assume every HTTP request has one.
- **When investigating any specific request, the user-feedback records for that ID are part of the minimum query set — every time.** Query them in the same batch as the run and stage records, and **read the free-text comment**, not just the rating. Seeing that a feedback event *exists* in a log stream isn't the same as reading what it *says*; positive ratings can still carry bug reports; and feedback routinely describes problems the error codes never show. "I already checked the run, stage, and application logs" is never a reason to skip it — it's a different check, not a subset of those.
- **Schema/design docs versus reality**: when a design document and the actual schema disagree, the schema is ground truth; note the stale document.

## Stack Detection & Adaptation

Before adding or changing any logging, inspect the project to find what's already there:

- Search for existing logger imports/config (`winston`, `pino`, `logging.getLogger`, `structlog`, `zap`, `logrus`, `slog`, `slf4j`, `Serilog`, `ILogger`) and for any centralized logger setup/wrapper module the project has already standardized on.
- Check for existing log format conventions (JSON vs. plain text), existing correlation-ID/middleware patterns, and any log-level configuration (env var, config file) already wired up.
- If a logging library and convention already exist, use them — do not introduce a second logging library or a competing pattern, even if a different tool would be a stronger choice in isolation.
- If no logging library exists yet, adopt the idiomatic default for the detected language/framework (see Technical Skill Set above) rather than raw print statements, and set it up minimally rather than over-engineering a full observability stack unprompted.
- This same detection pass feeds the project-context signal used by the orchestrator's 3-signal model — the presence (or absence) of an established logging convention is itself a trigger for this skill to activate on the current task.
