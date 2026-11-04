---
name: requirements-engineering
description: "The requirement-clarity gate before implementation: ambiguity detection, EARS, acceptance criteria, NFRs, disciplined questions, spec and plan templates. Use when a request is vague or needs a spec."
metadata:
  title: "Requirements Engineering"
  category: "Process & Governance"
  tier: practice
  trigger_keywords: "requirement, requirements, ambiguous request, clarify scope, acceptance criteria, EARS, user story, non-functional requirement, NFR, spec, specification, elicitation, out of scope, definition of done"
---

## Role Identity

Owns the step between "someone asked for something" and "we know exactly what correct looks like." Elicitation is the most communication-heavy and most consequential activity in the lifecycle, and it is where an agent has the most leverage. The central reframe: **ambiguity is a resource, not a defect** — each one points at knowledge the requester holds and hasn't voiced. The dangerous case is never an ambiguity that was noticed; it's one that was resolved silently, and wrongly, without anyone realising a choice was made.

## Responsibilities

### 1. Choose the elicitation technique that fits

| Technique | Fits when | Produces |
|---|---|---|
| Structured interview | Stakeholder available, domain unfamiliar | Depth; tacit knowledge; ambiguity cues |
| Workshop | Several stakeholders who disagree | Early conflict; shared vocabulary |
| Observation | The stated process differs from the real one | Undocumented workarounds |
| Document analysis | Legacy or regulated systems | Constraints; existing contracts; data shapes |
| Prototype / wireframe | Stakeholder can't say what they want | Reaction-driven requirements |
| Use cases / scenarios | Behaviour-heavy systems | Flows; actors; alternate paths |
| Event storming | Complex domain, many integrations | Domain events; bounded contexts; ownership |
| Analogue analysis | Greenfield product | Table-stakes expectations |
| Survey | Many users, shallow depth | Prioritisation signal |
| Telemetry & tickets | Brownfield | What users actually do versus say |

In a single-user agent session the dominant three are usually: asking the requester directly, reading what already exists (code, docs, decision records, past feedback), and mining telemetry (logs, error records, user-feedback data).

### 2. Detect ambiguity systematically

| Type | Example | Cue |
|---|---|---|
| Lexical / polysemy | "account", "order", "user" meaning different things to different people | Same noun, different collocations |
| Syntactic / attachment | "notify the manager and the admin who approved it" | Coordination + relative clause |
| Referential | "then it should update the record" | Pronoun with no clear antecedent |
| Vagueness | fast, robust, user-friendly, appropriate | Unquantified adjective/adverb |
| Scope / quantifier | "all users can see their reports" | all/any/each over an undefined set |
| Incompleteness | Happy path only | No "what if" branches |
| Cross-domain | A term meaning one thing to the business and another to engineering | Two vocabularies colliding |
| Pragmatic | Literally clear, but the *why* is missing | No traceable goal |
| Temporal | "immediately", "eventually", "after processing" | Time words without bounds |
| Harmless vs harmful | Some ambiguity deliberately leaves design freedom | Would two readings produce different implementations? |

**The escalation test:** would two reasonable readings produce different code, different tests, or different data? No → record the interpretation as an `ASSUMPTION` and continue. Yes → it's a blocking question; stop.

**Mechanical red flags** to scan any request for: comparatives with no baseline ("faster"); superlatives ("optimal"); open-ended lists ("etc.", "including but not limited to"); subjective adjectives ("intuitive", "seamless"); weak modal verbs ("should", "may"); several behaviours joined by "and"; passive voice hiding the actor ("the data shall be validated" — by what?); negative-only requirements; implementation prescribed inside a requirement; escape hatches ("where appropriate", "if practical"). Terms to flag on sight: *appropriate, timely, efficient, user-friendly, properly, various, robust, seamless, intuitive, fast, quickly, immediately, eventually, soon, periodically, reasonable.*

**Semantic checks:** one noun used differently by two stakeholders · a requirement with no traceable goal · two requirements that can't both hold · a state that can't be reached or can't be left · a happy path with no failure path.

For every flag, generate a **closed, decidable question** — one whose answer eliminates at least one candidate implementation.

### 3. Hold each requirement to seven quality criteria (ISO/IEC/IEEE 29148)

Unambiguous · Consistent · Complete · Singular (one requirement per statement) · Feasible · Traceable (up to a goal, down to design and tests) · Verifiable (some test can decide pass/fail). A requirement failing any one is rewritten or escalated.

### 4. Write requirements in EARS form

EARS (Easy Approach to Requirements Syntax, Rolls-Royce, 2009): zero or more preconditions, at most one trigger, one system, one or more responses — always in that order.

| Pattern | Template | Implies code shape | Implies test shape |
|---|---|---|---|
| Ubiquitous | The `<system>` shall `<response>` | Invariant / assertion | Property test |
| Event-driven | When `<trigger>`, the `<system>` shall `<response>` | Handler | Integration test |
| State-driven | While `<state>`, the `<system>` shall `<response>` | State machine | State-transition test |
| Unwanted behaviour | If `<condition>`, then the `<system>` shall `<response>` | Error path / guard | Negative test |
| Optional feature | Where `<feature>`, the `<system>` shall `<response>` | Feature flag | Conditional suite |
| Complex | Combinations of the above | — | — |

The **unwanted-behaviour** pattern is the one most reliably forgotten. A codebase full of deterministic guard functions is, in EARS terms, a codebase full of "If…then…shall" requirements made executable — name them that way in their docstrings. Grammar: `shall` (not should/will/must); one behaviour per statement; concrete values ("within 1 s", not "quickly"). Caveat: EARS constrains syntax, not correctness — pair it with Given/When/Then examples carrying real data.

### 5. Shape backlog items with INVEST and separate acceptance criteria from Definition of Done

INVEST: **I**ndependent · **N**egotiable (states outcome, not implementation) · **V**aluable · **E**stimable · **S**mall · **T**estable. An item that raises significant questions in refinement is held back until they're answered. For the backlog as a whole, DEEP: **D**etailed appropriately, **E**stimated, **E**mergent, **P**rioritised.

| | Acceptance criteria | Definition of Done |
|---|---|---|
| Scope | One item | Every item |
| Says | What must be true for *this* behaviour | What must be true for *anything* to ship |
| Example | "Reset link expires after 30 minutes" | "Reviewed; tests pass; docs updated; no new critical findings" |

An item can meet all its acceptance criteria and still fail the Definition of Done — then it isn't shippable. See `templates/definition-of-done.md`.

### 6. State non-functional requirements across ISO/IEC 25010:2023

If a functional requirement is a verb, NFRs are its adverbs. The 2023 model has nine characteristics (adding *safety*, renaming *usability* → *interaction capability* and *portability* → *flexibility*):

| Characteristic | Typical NFR shape |
|---|---|
| Functional suitability | "Results match the reference implementation to 6 decimal places" |
| Performance efficiency | "p95 latency < 800 ms at 2,000 rps" |
| Compatibility | "Coexists with v1 on the same host" |
| Interaction capability | "WCAG 2.2 AA conformance" |
| Reliability | "99.9% monthly availability; RTO 5 min; RPO 1 min" |
| Security | "PII encrypted at rest with customer-managed keys" |
| Maintainability | "No module exceeds cyclomatic complexity 15" |
| Flexibility | "Scales horizontally to 50 nodes without config change" |
| Safety | "On sensor loss, enters a defined safe state within 200 ms" |

The standard omits four characteristics many real systems care about — **deployability, observability, cost efficiency, energy efficiency**. Add them explicitly when relevant (cost efficiency, for example, is first-class for anything metered per token, per call, or per GB). Mark any characteristic that doesn't apply as an explicit N/A rather than leaving it blank.

### 7. Maintain traceability

Every requirement links **up** to a goal, **sideways** to requirements it conflicts with or depends on, and **down** to design, code, and tests — so "what breaks if this changes?" and "is this actually tested?" are answerable. Atomic requirements trace cleanly; compound ones end up with gaps.

### 8. Enforce the clarity gate

No item enters implementation until all of these pass:

| # | Check | If it fails |
|---|---|---|
| 1 | Goal stated — outcome, for whom, why | Ask; don't infer the *why* |
| 2 | Scope bounded, with an explicit **out-of-scope** list | Propose boundaries, confirm |
| 3 | Every requirement meets the seven criteria (§3) | Rewrite or ask |
| 4 | Requirements in EARS or Given/When/Then with concrete data | Rewrite |
| 5 | Unwanted-behaviour / error paths specified | Ask — most-forgotten category |
| 6 | Acceptance criteria written, testable, agreed | Draft and confirm |
| 7 | NFRs stated across §6, with explicit N/As | Propose defaults, confirm |
| 8 | Glossary covers every ambiguous term; cross-domain collisions flagged | Build it |
| 9 | Dependencies and integration points identified | Investigate |
| 10 | Assumptions logged with owners | Log |
| 11 | Definition of Done agreed | Confirm |
| 12 | Every blocking ambiguity resolved | **Stop. Ask.** |

Apply it proportionally: a one-line bug report rarely needs a spec document; a new subsystem or a cross-cutting behaviour change does.

### 9. Ask well

- **Batch** questions and ask at a checkpoint, not one at a time.
- **Rank by decision impact** — lead with what changes the most.
- **Propose a default for each** ("I'll assume X unless you say otherwise") — cheaper to answer, and silence can confirm a good guess.
- **Show consequences** ("If A: a queue, ~3 days. If B: a direct call, ~4 hours.").
- **Cap at about seven** — more means you didn't rank, so investigate more and ask less.
- **Never ask what's findable** in the code, schema, git history, or logs.
- **Tag** each question `BLOCKING` or `CONFIRM`.

## Technical Skill Set

EARS; Given/When/Then (Gherkin) scenarios; ISO/IEC/IEEE 29148 requirement quality; ISO/IEC 25010:2023 quality model; INVEST/DEEP; event storming; lightweight glossary and assumption-log maintenance; requirement-to-test traceability matrices.

**Worked example.** Raw request: *"Users should be able to drag tasks between columns. It needs to work offline too. Handle errors gracefully."* Flags: "gracefully" (vague); "work offline" (unbounded — read-only? full writes? for how long? conflict policy?); no failure path; no persistence semantics; "users" unscoped. Ranked blocking questions with defaults: offline scope (*default: full offline writes, last-write-wins* — consequence ~1 day vs ~2 weeks); conflict policy (*default: user-resolved dialog*); offline retention window (*default: 7 days*); side effects of a move and when they fire (*default: on sync only*). Resulting requirements:

- REQ-001 (Event) — When the user drops a task card on a different column, the system shall set the task's status to that column's status.
- REQ-002 (State) — While the client is offline, the system shall store status changes locally and mark them pending synchronisation.
- REQ-003 (Event) — When connectivity returns, the system shall synchronise pending changes within 10 seconds.
- REQ-004 (Unwanted) — If a synchronisation conflict occurs, then the system shall show a dialog presenting both versions.
- REQ-005 (Unwanted) — If synchronisation fails after 3 retries, then the system shall keep the local change and show a persistent sync-failure indicator.
- REQ-006 (Ubiquitous) — The system shall log each status transition with actor, timestamp, and source (online/offline).

The questions that mattered most were about scope and cost, not syntax.

## Decision-Making Lens

Optimises for **eliminating wrong implementations before any are written**. A question is worth asking only if its answer removes a candidate implementation; a requirement is worth writing only if a test could fail it. Between asking and assuming, it assumes — explicitly and on the record — whenever the two-readings test says the difference doesn't matter.

## Trigger Signals

- **Keywords**: requirement, spec, acceptance criteria, user story, scope, out of scope, NFR, "what exactly should it do", "make it work offline/fast/robust" (any vague quality word).
- **File/path signals**: `docs/specs/`, `docs/adr/`, `*.feature`, PRD/spec markdown files, issue/ticket text pasted into the conversation.
- **Project-context signals**: a request for a new feature or behaviour change with no stated acceptance criteria; conflicting instructions across a conversation; a request containing flagged vague terms.

## Collaboration Behavior

- **Upstream of everything**: runs before `software-architect`, `backend-developer`, `frontend-developer`, and friends touch code — the clarity gate is state 2 of `agent-operating-principles`' phase machine.
- **Parallel with `technical-product-manager`** on the *why* and prioritisation; this skill owns precision and testability, the PM owns value and ordering.
- **Hands off to `testing-strategy` / `qa-test-engineer`** the acceptance criteria and unwanted-behaviour requirements, which become the test plan's backbone.
- **Debates** any role that wants to start building before blocking questions are answered.

## Output Style / Conventions

- Requirements as numbered EARS statements (`REQ-###`), acceptance criteria as Given/When/Then (`AC-###`) mapped to requirement IDs.
- Questions batched, ranked, tagged `BLOCKING`/`CONFIRM`, each with a default and a consequence.
- An explicit out-of-scope list in every spec — never empty.
- Assumptions in a table: ID, assumption, impact if wrong, owner, status.

## Anti-Patterns

- Resolving an ambiguity silently.
- Asking open questions with no proposed default.
- Interrogating the requester about facts the repository could answer.
- Specifying only the happy path.
- Writing requirements that prescribe implementation ("use Redis") instead of outcome.
- Treating a vague adjective as a requirement.
- Running a full spec ritual for a trivial change — or skipping the gate on a consequential one.

## Stack Detection & Adaptation

Look for where the project already keeps requirements and decisions — `docs/`, `docs/adr/`, an `.ai/` memory folder, `*.feature` files, a PRD directory, issue templates under `.github/` — and write specs and decision records there in the existing format. If nothing exists, use the templates in this skill's `templates/` folder, placed wherever the project keeps durable docs. Match acceptance-criteria style to the detected test tooling (Gherkin where a BDD runner exists; plain Given/When/Then tables otherwise).

## Templates

| File | Use |
|---|---|
| `templates/spec-template.md` | Full specification: problem, goal, scope, glossary, actors, EARS requirements, NFRs, acceptance criteria, data, interfaces, assumptions, questions, risks, DoD |
| `templates/clarification-question-bank.md` | Prompts to run against any new request so nothing important is forgotten |
| `templates/definition-of-done.md` | Universal per-item shipping checklist |
| `templates/adr-template.md` | Architecture decision record |
| `templates/pr-template.md` | Pull-request description tied to spec and verification evidence |
| `templates/postmortem-template.md` | Blameless incident review |
| `templates/agents-md-template.md` | Short, specific agent-instruction file for a repository |
| `templates/agent-system-prompt-skeleton.md` | Condensed constitution for an autonomous engineering agent |
| `templates/autonomous-plan.md` | Plan an agent executes on its own after a "go": phases with exit checks, an exhaustive STOP-conditions list, auto-handled-and-logged everything else, a Definition of Done tied to the spec's success criteria, fact-only final report |
