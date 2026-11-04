# Autonomous Execution Plan: <work item>

This file is written **as instructions to the executing agent**. Read `<spec file>` first for
context, then execute the phases below in order.

## Trigger

When the human says **"go"**, execute Phases 0 through <N> sequentially, without pausing for
confirmation between phases. Stop and ask **only** when a STOP condition below is hit — those are
the only expected interruptions. Otherwise work autonomously and deliver the final report at the
end.

## STOP conditions (the only times to interrupt and wait)

List every one explicitly; anything not listed here is handled automatically.

1. **Missing or placeholder inputs** — a required credential, config value, or input file is
   absent or still a placeholder (`<...>`, `changeme`, an example value). Print exactly what is
   missing and stop. Never fabricate values or proceed without them.
2. **Non-transient smoke-test failure** — the Phase <k> smoke test fails for a reason that is not
   a transient network error (e.g. 401/403, 404 model/resource not found, schema mismatch). Print
   the exact error and stop; it needs a human decision.
3. **Failure rate above threshold** — after all retries, more than <X>% of <units> failed. Stop and
   report which failed and why, rather than producing results from incomplete data.
4. **Anything Red-tier** — any action the project classifies as needing explicit confirmation
   (destructive data operations, production deploys, secret/IAM changes, spending above
   <budget>, writing outside the agreed scope). Describe the action and stop.
5. <project-specific condition, if any>

**Everything else** — transient timeouts, individually retryable failures, formatting, minor
tool hiccups — is handled automatically per the retry/error rules in `<module or section>`, and
**logged** (what happened, what was done) for the final report.

## Phase 0 — Environment setup

1. <check/create config from its example; missing real values → STOP 1>
2. <create/activate the environment; install pinned dependencies>

**Exit check:** <command> succeeds; <expected state>.

## Phase 1 — Validate configuration

1. <run the config validator; it must exit non-zero on any missing/placeholder value → STOP 1>

**Exit check:** validator exits 0.

## Phase 2 — Smoke test (fail fast before the full run)

1. <one minimal call per external dependency; print the raw parsed result>
2. Non-transient failure → STOP 2. Success → continue automatically.

**Exit check:** every dependency returned a valid result.

## Phase 3 — Main run

1. <the real work, with per-unit retries>
2. Failure rate above <X>% → STOP 3.

**Exit check:** <output file> exists, has <expected count> rows/items, failure rate ≤ <X>%.

## Phase 4 — Produce outputs

1. <generate report/artifacts; include an explicit "Limitations" section — sample size,
   placeholder constants to verify, single-run measurements>
2. Verify every output file exists and is non-empty before declaring success.

**Exit check:** <files> exist and are non-empty.

## Phase <N> — Final report to the human

Print a short summary containing:
- Where every output lives (paths)
- The headline numbers/results
- Anything excluded or degraded (failed units below the threshold, skipped steps) and why
- Anything the human must verify before relying on the results (e.g. placeholder pricing)
- The log of automatically handled issues, condensed

**Report facts; don't editorialize.** State the numbers and what happened; don't declare
winners, recommend decisions, or soften failures — let the human draw conclusions.

## Definition of Done

Every success criterion in `<spec file>` §<n> is satisfied (list them, each with how it is
verified), every phase's exit check passed, and the final report has been delivered.

| Success criterion (from spec) | Verified by |
|---|---|
| <criterion> | <command / file / check> |
