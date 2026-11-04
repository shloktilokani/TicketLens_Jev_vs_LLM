## What and why
One paragraph a reviewer can check against the code: what changed, and the reason.

## Traceability
- Spec: <link or "none — small change">
- Requirements implemented: REQ-…
- Acceptance criteria met: AC-… (test: `<path::test_name>`)
- Acceptance criteria **not** met, and why: <or "none">

## Approach
The design choice made and the main alternative rejected. Link an ADR if architecturally significant.

## Verification
- Tests added/changed:
- Observed red → green: <yes — include the failing output>
- Manual / exploratory checks performed:
- **Not verified** (mandatory — what a reviewer should check by hand):

## Risk
- Blast radius:
- Reversibility:
- Migration: <none | link — reversible yes/no>
- Feature flag: <none | name, default off>
- Rollback steps:

## Open assumptions
| ID | Assumption | Impact if wrong |
|---|---|---|
