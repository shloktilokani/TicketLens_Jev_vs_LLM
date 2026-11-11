# CLAUDE.md

TicketLens_Jev_vs_LLM: local single-user app comparing Jev and an LLM on ShopKart ticket classification. It runs on local models (AutoTrust JEV and an Ollama LLM); the paid APIs, hosted Jev and OpenAI, are deferred by owner decision.

@AGENTS.md

Status and handover: `.context/PROGRESS.md` (start there). How the app works: `.context/architecture.md` and `.context/data-model.md`.

**Code size:** apply the `ponytail` skill (level `full`) to every coding, development and database task, and follow `.context/code-size-standards.md`. Never cut security, validation, tests or required behaviour to save lines.

## Commands (from the repository root)

```bash
backend/.venv/bin/pytest backend -q
backend/.venv/bin/ruff check backend
npm --prefix frontend run lint
npm --prefix frontend run build
npm --prefix e2e test        # browser tests on an isolated stack; add -- --headed to watch
```

Run the app: `README.md`, "Run it locally" (quick start), and `SETUP.md` for the full steps and troubleshooting.

<!-- BEGIN skillpack (generated; edit outside this block; re-run skillpack to refresh) -->
## Engineering skills library

Skills live in `.claude/skills/` and are listed to you automatically.

1. **Route first.** For any non-trivial task, read `.claude/skills/_orchestrator/SKILL.md` and apply its 3-signal routing (task keywords, files touched, detected stack): load a skill when 2 of 3 signals point to it.
2. **Always apply the constitution:** `agent-operating-principles` (investigate before building; evidence over recall) and `agent-verification-and-guardrails` (observed red-to-green tests; a *not verified* section in every completion report; permission tiers).
3. **Non-negotiable:** `codebase-security-auditor` applies on any single signal. Secrets, credentials, PII, and proprietary code never leave the machine without the user's explicit, specific confirmation.
4. **When several skills apply,** weigh them internally and give one synthesized answer. Tiebreak: production safety/data integrity > user-facing correctness > security hardening > performance > convenience.
5. **Ask before Red-tier actions:** merges to main, production deploys, schema migrations, live-database writes, deleting data, IAM/secret changes, public contract changes. Never weaken or delete tests to get green.
6. **Project tailoring** lives only between `<!-- project-tailoring:begin -->` and `<!-- project-tailoring:end -->` at the end of a SKILL.md, or in the skill's `project/` folder. `skillpack` preserves both when it updates skills.

<!-- END skillpack -->
