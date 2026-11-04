# Clarification Question Bank

Run these prompts against any new request to build its question set. Most won't apply to a
given request — the point is that nothing important is skipped. Keep only questions whose
answers would change the implementation, rank them by impact, give each a default, and ask
no more than about seven at once.

## Purpose and value
- What problem does this solve, and for whom? What happens if it isn't built?
- How will we know it worked? Which number moves?
- Is this the underlying need, or one proposed solution to an unstated need?

## Scope
- What is explicitly out of scope?
- Every user, or a segment? Every environment, tenant, region?
- Does it replace something? What happens to the old path and its data?
- Is there a deadline, and what drives it?

## Behaviour
- Walk the happy path step by step.
- What are the failure cases, and what does the user see in each?
- Concurrent access? Double submission? Retries?
- Zero items? One? Ten thousand?
- Is anything here idempotency-critical (payments, messages, external side effects)?
- What must be logged or audited?

## Data
- What is created, read, updated, deleted?
- Is any of it personal or regulated? Retention? Residency?
- If two systems disagree, which is the source of truth?
- Does existing data need migrating or backfilling?

## Integration
- What does this depend on? What happens when each dependency is slow or down?
- Which existing contracts must not break, and who consumes them?
- Rate limits, quotas, or per-call costs?

## Non-functional
- Volume now and in a year? Peak versus average?
- Acceptable latency? Acceptable downtime? RTO / RPO?
- Who is allowed to do this, and where is that enforced?
- Accessibility, localisation, offline needs?

## Operational
- How will we know in production that it's working — or broken?
- Is it reversible? What is the rollback plan?
- Who owns it on call? Does it need a runbook?
- Should it sit behind a flag? Who decides when it turns on?

## Constraints
- Technology that must — or must not — be used?
- Compliance, contractual, or legal constraints?
- Prior decisions (ADRs) that constrain the design?
- Other in-flight work touching the same code?
