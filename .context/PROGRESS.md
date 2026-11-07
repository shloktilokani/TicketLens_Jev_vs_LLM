# Progress

Build order and acceptance criteria: `implementation.md`. Update this file after every phase.

## Status

Phases 0 and 1 are complete. **Next: Phase 2**, which needs MongoDB installed by the operator.

Plain-language phase order and every step that needs the owner: `ROADMAP.md`.

## Phases

- [x] Phase 0: Repository and agent setup
- [x] Phase 1: Scaffold the frontend and backend
- [ ] Phase 2: Local configuration and MongoDB connectivity
- [ ] Phase 3: Domain schemas and taxonomy
- [ ] Phase 4: Ticket CRUD and sequential IDs
- [ ] Phase 5: Frontend shell and design system
- [ ] Phase 6: Ticket screens
- [ ] Phase 7: CSV template, import, and export
- [ ] Phase 8: Provider adapter contracts and mock mode
- [ ] Phase 9: Jev integration
- [ ] Phase 10: GPT integration
- [ ] Phase 11: Execution history and cost logging
- [ ] Phase 12: Comparison workflow
- [ ] Phase 13: Bulk processing
- [ ] Phase 14: Evaluation dataset and analytics
- [ ] Phase 15: Settings page
- [ ] Phase 16: Testing, reliability, and security review
- [ ] Phase 17: Local release and documentation
- [ ] Phase 18: Deployment readiness

## Blockers

- **Phase 2:** MongoDB Community Edition is not installed on this machine. The operator installs and starts it.
- **Phases 9 and 10, real calls only:** `TYPESAFE_API_KEY` and `OPENAI_API_KEY` go in `backend/.env`. Mock mode covers development until then.
- **Phase 10:** `OPENAI_MODEL` has no default in `.env.example` and must be chosen.

## Required fix before any paid evaluation (Phase 14)

`sample_tickets_100.csv` is kept exactly as supplied, but it must not be used for evaluation yet:

- In all 100 rows, `title` is identical to `expected_subcategory`. Titles are sent to both providers, so this leaks a ground-truth label and breaks the rule in `AGENTS.md`.
- No row uses Hindi in Devanagari script. About 30 rows look like romanised Hindi or Hinglish; the spec asks for English, Hindi and Hinglish.

Create a corrected dataset in Phase 14 with realistic titles and real Hindi tickets, keeping the labels and the 100-row size. The owner reviews it before any paid run.

## Assumptions and spec gaps

- `evaluation_labels` is required by `data-model.md` but missing from the list in `architecture.md` section 8. It is included.
- `Running` is used in `architecture.md` but missing from the status list in `requirements.md`. It is treated as an in-progress status.
- `BULK_CONCURRENCY` and `JEV_ESCALATION_THRESHOLD` appear in both env and settings. Env seeds the default; `app_settings` overrides it.
- `final_classification` is populated in the `data-model.md` example, but its notes say null until selected. The notes are followed.
- Spec and status docs live in `.context/` at the owner's request; `README.md`, `AGENTS.md` and `CLAUDE.md` stay in the root. The layout in `implementation.md` is updated to match, and its root `docs/` folder is dropped.
- Bare file names inside `.context/` refer to files in that same folder. Phase 7's template download reads `.context/sample_tickets_template.csv`.
- `.env.example` lives at `backend/.env.example` (Phase 1 layout), not the repository root.
- Playwright is the assumed tool for Phase 16 end-to-end tests.
- UNCONFIRMED: the owner's "phase 120" was read as Phases 0 to 1.

## Phase 1 notes

**Tests run:** backend `pytest` (2 passed) and `ruff`; frontend `eslint`, `prettier --check`, `tsc` and `vite build`. Both servers were started with no `.env` and MongoDB not running: `/docs` and the frontend returned 200 and both bound to loopback only.

**Choices:**
- TypeScript is 6.0.x, not the template's 7.0.2. `typescript-eslint` 8.72 supports only versions below 6.1. Revisit when it supports 7.
- The system font stack replaces shadcn's default Geist font, as `design.md` asks.
- `react-refresh/only-export-components` is off for `src/components/ui` only, because shadcn exports variants beside components.
- The OpenAI SDK is added in Phase 10, when it is first used.

**Dependency review (2026-11-04):**
- `pip-audit` on `backend/requirements.txt`: no known vulnerabilities.
- `npm audit --omit=dev`: 0 vulnerabilities in production dependencies.
- `npm audit`, all dependencies: 15 (2 low, 13 moderate), from `minimatch` (ESLint, typescript-eslint and ts-morph chains) and `deepmerge` (shadcn CLI). Accepted: dev tools only, not in the browser bundle, no untrusted input. npm's only fixes are downgrades to older majors.
- `cn` was added by shadcn and replaces `clsx` + `tailwind-merge`. It is MIT-licensed, published by shadcn from `shadcn-ui/cn`, used in shadcn's own install docs, and has no install script. A string scan found no network, env or exec use.

**Known warning:** pytest reports `StarletteDeprecationWarning` about `httpx` in `starlette.testclient`. It is harmless today; check it when upgrading FastAPI.

## Code size requirement (2026-11-07)

The owner requires a small, clean codebase without losing functionality or security. Rules, evidence and enforcement are in `code-size-standards.md`. `ponytail` is installed and always on for coding tasks. Lint limits: ruff `C90` (complexity 10) and `SIM`; ESLint `complexity: 10`.

## Skills

32 skills are installed in `.claude/skills/` from Claude_Skills commit `058b511`. Reasons for exclusions are in the `_orchestrator` tailoring block. Project-specific notes live only in tailoring blocks.

The skill drift hook is left out because `~/Projects/Claude_Skills` has 65 untracked `SKILL (1).md` files, which make its skill hashes differ. Run `skillpack` from a clean clone, or remove those files first.
