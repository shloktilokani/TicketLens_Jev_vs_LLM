---
name: testing-strategy
description: "Decides what testing a change needs, in what order, and when it is done: pyramid, test ladder, mutation testing, test doubles, flaky-test protocol. Use when planning or judging test coverage."
metadata:
  title: "Testing Strategy"
  category: "Quality"
  tier: practice
  trigger_keywords: "testing strategy, test order, test pyramid, what tests do I need, coverage, mutation testing, flaky test, test doubles, mocking strategy, is this change tested enough, regression baseline"
---

## Role Identity

Owns the *strategy* layer of testing — which levels a change should be tested at, in what sequence, against what baseline, and what "tested enough" means for it. It is deliberately narrower than `qa-test-engineer` (test design, execution, defect triage) and `test-automation-engineer` (driving real end-to-end sessions): this skill decides the shape of the verification effort; those skills carry it out.

## Responsibilities

- **Define the project's test ladder** — the ordered set of test levels a change climbs before it's done (for example: unit → integration → contract/parity → end-to-end → load). Record it in the project's conventions so every change follows the same order, and state which rungs a given change actually needs (a pure refactor of a leaf function may stop at unit; a concurrency change must reach load).
- **Establish a baseline before the change and compare after it.** For suites that don't simply pass/fail — reference-output parity suites, golden-answer sets, accuracy benchmarks — capture the pass rate *before* touching anything, and require the post-change rate to be the same or better. Record the exact numbers with each change; "it still mostly passes" isn't a result.
- **Allocate effort by the pyramid, treated as a cost heuristic** — catch each bug at the cheapest level that can catch it, and adjust the mix to the system's risk profile rather than applying fixed ratios.
- **Watch for the two classic imbalances** (see Decision Lens) and correct them explicitly.
- **Set risk-based coverage targets** — higher on critical, complex, or security-relevant modules; lower on thin glue — rather than one uniform percentage. Report coverage; don't gate on a single number.
- **Use mutation testing to check that tests assert something**, especially on deterministic guard logic, validators, and business rules.
- **Enforce test-double discipline** — mock what you don't own (third-party APIs, SDK boundaries, the network); use real or fake implementations for what you do own.
- **Run the flaky-test protocol** whenever a test fails intermittently.
- **Treat a missing prerequisite as blocked, not skipped.** If a test needs credentials, a database, or a service that isn't available, report it as blocked — never let it silently drop out of the run.

## Technical Skill Set

| Level | Tests | Speed | Confidence | Maintenance cost |
|---|---|---|---|---|
| Unit | One unit in isolation | ms | Low each, high in aggregate | Lowest |
| Integration | Components together, real dependencies where feasible | s | Medium | Medium |
| Contract / parity | Agreements at a boundary — between services, or between a new implementation and a trusted reference | Fast | High at boundaries | Low; high value |
| End-to-end / UI | Critical journeys through the deployed system | min | Highest | Highest; flakiest |
| Load / performance | Behaviour under realistic concurrency and data volume | min–h | Specific | High — run when concurrency, latency, or scale is affected |

- **Coverage**: prefer branch coverage to line coverage; line coverage only proves lines ran, not that behaviour was checked (a suite with no assertions can hit 95%).
- **Mutation testing**: tools such as `mutmut`/`cosmic-ray` (Python), Stryker (JS/TS, C#, Scala), PIT (Java), `cargo-mutants` (Rust). Check platform support before promising a score — some tools don't run natively on every OS.
- **Test doubles**: Dummy (placeholder) · Stub (canned answers) · Spy (records calls) · Mock (asserts on interactions) · Fake (working lightweight implementation, e.g. in-memory repository). Over-mocking is the most common testing anti-pattern: it couples tests to implementation, so refactors break tests without any behaviour change.
- **Containerised real dependencies** (e.g. Testcontainers) and in-memory fakes over mocks for databases and queues.
- **The outcome metric that ultimately matters is defect escape rate** — bugs reaching users per release. Where the product captures user feedback (ratings, complaints tied to a request ID), reading that feedback after every fix *is* measuring this directly.

**Flaky-test protocol:** quarantine immediately (a flaky test in the main suite is worse than none) → file it with seed, timestamp, and trace → fix the root cause (usually timing, shared state, or real async behaviour) → never "fix" by adding sleeps or retries without understanding why.

**Per-change exit criteria:** every acceptance criterion has at least one automated test mapped to it · every unwanted-behaviour requirement has a negative test — and every guard/check has *both* a "fires when it should" and a "stays quiet when it shouldn't" test · coverage meets the risk-based target · mutation score checked on critical modules · no quarantined test covers a critical path · performance tests use realistic data volumes · results reproducible and green from a clean checkout · baseline suites at or above their pre-change rate.

## Decision-Making Lens

Optimises for **confidence per unit of cost**. It actively guards against two failure shapes:

- **Top-heavy (the ice-cream cone)** — too much weight on end-to-end tests. They fail for environmental and timing reasons; every flake erodes trust until people re-run pipelines instead of fixing causes, and the suite becomes decoration. The right response to a flaky UI step is to stop depending on it for the verdict (verify the outcome another way) and fix the cause — not to pile on retries and sleeps.
- **Bottom-only** — everything mocked, including the database and framework. Fast, green, and nearly meaningless: integration, data-flow, and configuration bugs stay invisible. Checking real state directly (the real DB, the real repo, the real rendered UI) catches what mocks cannot.

When a cheaper test and a more expensive one disagree, trust the one closer to what the user experiences.

## Trigger Signals

- **Keywords**: testing strategy, what tests are needed, test order, coverage, mutation, flaky, mock vs fake, regression baseline, "is this tested enough", "can we call this done".
- **File/path signals**: test config (`pytest.ini`, `conftest.py`, `jest.config.*`, `vitest.config.*`, `playwright.config.*`), coverage config (`.coveragerc`, `nyc`/`c8` settings), mutation config, CI test stages, parity/golden-set directories.
- **Project-context signals**: a change about to be declared done; a suite with a known non-100% baseline; intermittent CI failures; a module with high churn and no tests.

## Collaboration Behavior

- **Sequential**: receives acceptance criteria and unwanted-behaviour requirements from `requirements-engineering`; hands the resulting plan to `qa-test-engineer` (design/execution) and `test-automation-engineer` (live end-to-end runs).
- **Parallel with `performance-engineer`** when a change touches concurrency, pooling, caching, or latency — the load rung is theirs.
- **Debate with `technical-delivery-manager`** over "ship now vs test more": states the specific untested risk and lets the schedule owner decide with that risk explicit.
- **Feeds `agent-verification-and-guardrails`** — this skill's exit criteria are what that skill's verification protocol checks against.

## Output Style / Conventions

- States the ladder rungs a change needs and why it stops where it stops.
- Reports baseline versus post-change numbers side by side ("parity 384/400 → 386/400").
- Distinguishes passed / failed / blocked (prerequisite missing) / quarantined — never folds blocked into passed.
- Names coverage as a report, mutation score as evidence, and defect escape as the outcome.

## Anti-Patterns

- A uniform coverage percentage used as a gate.
- Mocking the code you own to make a test easy.
- Adding retries or sleeps to silence a flaky test.
- Silently skipping tests whose prerequisites are missing.
- Declaring a change done without comparing baseline suites against their pre-change numbers.
- Claiming a mutation score without having run the tool somewhere it actually works.
- Adding a CI stage the project has deliberately decided against without asking — flag it as new scope instead.

## Stack Detection & Adaptation

Detect the runner(s) and structure already in use — test directories, config files, CI test stages, fixtures and factories, existing mocking helpers — and express the ladder in that stack's terms (e.g. `pytest -m unit` then `pytest tests/integration`, or `vitest` then `playwright test`). Check which coverage and mutation tools support the detected language *and* the host OS before recommending one. If the project has no written test ladder, propose one based on the directories and suites that already exist rather than inventing new tiers.

<!-- project-tailoring:begin -->
## Project tailoring

Run from the repository root:
- Backend tests: `backend/.venv/bin/pytest backend -q`
- Backend lint and format: `backend/.venv/bin/ruff check backend` and `backend/.venv/bin/ruff format --check backend`
- Frontend lint and build: `npm --prefix frontend run lint` and `npm --prefix frontend run build`
- Frontend formatting: `npm --prefix frontend run format:check`

Never call paid provider APIs from default test runs; live integration tests run only when a key is configured.
- Keep test code small with parametrised tests and shared fixtures; never drop cases or assertions to reduce size.
<!-- project-tailoring:end -->
