# AGENTS.md

> Keep this short and concrete. Long, vague, or auto-generated instruction files make agents
> worse. Document only what differs from language/framework defaults.

## Overview
<Two sentences on what this is. Primary language and framework, with versions.>

## Commands
```bash
<install>            # exact command
<build>              # exact command and flags
<test>               # unit
<test:integration>   # prerequisites: <…>
<lint> / <format> / <typecheck>
<run:dev>
```

## Architecture
<3–6 bullets: module boundaries and what must not cross them.>
Decision records: <path> — read before proposing structural changes.

## Conventions that differ from defaults
- <e.g. "async/await only; no .then() chains">
- <e.g. "all DB access goes through repositories/; never from handlers/">
- <e.g. "errors are typed; never throw bare strings">

## Testing
<Where tests live, naming, how to run one test, coverage expectations, what needs integration tests.>

## Do not touch
<Generated files, vendored code, already-applied migrations, read-only reference trees.>

## Known quirks
- <quirk — and its workaround, so nobody "fixes" it>

## Git and PR conventions
<Branch naming, commit style, PR template, review rules, attribution policy.>

---
Placement: repository root beside `README.md`; in monorepos, additional files in
subdirectories (nearest file wins). Claude Code reads `CLAUDE.md` — to share one file, make
`CLAUDE.md` whose first line is `@AGENTS.md`. Keep tool-specific features (skills, hooks,
imports) in the native file and shared instructions here.
