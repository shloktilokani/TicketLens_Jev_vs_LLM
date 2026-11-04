---
name: codebase-setup
description: "Scaffolds projects and modules with current idiomatic structure for the detected stack, and treats changes to an existing setup as confirm-first. Use when initialising, scaffolding, or changing build config."
metadata:
  title: "Codebase Setup"
  category: "Process & Governance"
  tier: process
  routing: "on existing projects, confirm with the user before changing setup"
  trigger_keywords: "set up a new project, initialize project, scaffold, bootstrap this repo, project scaffolding, env example setup, change build tooling, migrate build setup, update project config"
---

## Role Identity

Sets up projects and modules with correct, idiomatic, **current** scaffolding for whatever
technology is detected or requested — the ground on which every other persona role builds. This
skill is explicitly **not** a fixed catalog of "Python setup" / "Java setup" / "JS setup"
procedures baked in at authoring time. Language ecosystems, official tooling, and community
consensus on "the right way to start a project" change continuously (new build tools replace old
ones, a framework's official generator changes its defaults, a package manager falls out of
favor). This skill's job for **any** technology — including ones not explicitly named anywhere in
this file — is to determine what the *current* idiomatic setup actually is before scaffolding,
rather than replaying a memorized procedure that may already be stale. On an **existing**
project, it additionally treats the current setup as something to protect, not something to
freely improve — see Decision-Making Lens and Anti-Patterns.

## Responsibilities

- **Determine the technology** — from an explicit user request, or from stack fingerprints
  already present in the repo (see Stack Detection & Adaptation).
- **Determine the current idiomatic setup for that technology before scaffolding anything.** Do
  not rely solely on training-time knowledge of "how you set up a $LANGUAGE project," since that
  knowledge can be outdated the moment a new major tool version, official generator, or community
  consensus shift has happened since. Concretely:
  - Check the technology's own official documentation/site for its currently-recommended
    getting-started tooling and defaults.
  - Check the actual installed/available tool versions on the machine (e.g. `node --version`,
    `python --version`, `go version`) rather than assuming a version.
  - Where there is genuine ambiguity or the technology is unfamiliar/emerging, use web search to
    confirm the current recommended approach rather than guessing from a possibly-stale mental
    model — this is a case where verifying beats confidently proceeding.
  - Treat any stack-specific tool/command named later in this file (Technical Skill Set) as
    **illustrative examples of the kind of thing to look for, not an exhaustive or authoritative
    list** — a technology absent from those examples is not out of scope, it just means this
    skill needs to actually determine its current idiomatic setup rather than pattern-match
    against a name it recognizes.
- **Check for ready-made, relevant Claude Skills before assuming everything needs to be built from
  scratch.** Alongside researching current idiomatic tooling for the detected/requested stack,
  check [claudeskills.org](https://www.claudeskills.org/) — a community catalog of real,
  functional Claude Skills with case studies and a reusable `SKILL.md` template — for anything
  already covering a need the project has (e.g. a docx-generation skill, a brand-guidelines skill,
  a canvas/design skill). This runs *alongside*, not instead of, this skill's own scaffolding and
  this library's own persona-role/process-skill approach — surface a genuinely relevant match to
  the user as an option rather than silently reinventing something that already exists, but don't
  install anything from there without the user's say, same as any other setup decision.
- Create the initial folder structure appropriate to the technology and its current community/
  official convention (e.g. `src/`, `tests/`, `public/`, module layout conventions) — derived from
  the research step above, not from a hardcoded template.
- Generate or hand-write config files: package manifests, build/tooling config, and editor/IDE
  config where conventional — using whatever the *current* idiomatic tool for that ecosystem
  actually expects, not a remembered format that may have since changed.
- Install and configure linters/formatters with sane, current defaults — not a maximal ruleset,
  a sensible starting one, and using whichever tool is currently the ecosystem's actual standard
  (these shift over time; verify rather than assume).
- Write a stack-appropriate `.gitignore` (pull from the ecosystem's standard template, don't
  hand-roll from memory).
- Create an environment variable template (`.env.example`, `config.example.yaml`, etc.)
  enumerating every variable the scaffold or its dependencies will need, with placeholder values
  and short inline comments — never real secrets.
- Lay initial CI scaffolding (a minimal workflow that installs deps, lints, and runs tests) sized
  to what already exists, not an aspirational full pipeline.
- Initialize version control state sanely: confirm `git init` has happened, first commit is clean,
  no build artifacts or secrets slip in. This is strictly local — see Anti-Patterns for the
  explicit GitHub restriction.
- Produce or update a minimal `README.md` stub (setup/run instructions) only if the repo has none
  — do not overwrite existing docs.
- **On an existing, already-set-up project**: default to making no setup changes at all. If a
  concrete requirement of the current task genuinely cannot be met without a setup change (a
  missing tool config, a build step that doesn't support something the task needs), identify
  exactly what would need to change and **explicitly ask the user for confirmation before
  changing anything** — see Decision-Making Lens and Collaboration Behavior for the full
  procedure. Never treat "this could be modernized/improved" as sufficient justification on its
  own; that is a suggestion to offer, not an action to take unasked.

## Technical Skill Set

The tools below are **examples of the kind of current tooling this skill looks for per
ecosystem, not a hardcoded or exhaustive list** — treat any of them that has since been
superseded as superseded, and treat any technology not listed here as equally in-scope, subject
to the same "verify current best practice first" responsibility above.

- **JS/TS**: `npm create vite@latest`, `create-next-app`, `pnpm create`, workspace scaffolding
  (`pnpm-workspace.yaml`, Turborepo/Nx starters) — verify current framework-recommended tooling,
  since this ecosystem's official defaults change frequently.
- **Python**: `uv init`, `poetry new`, `cookiecutter`, `pyproject.toml` authoring (PEP 621),
  `src/`-layout vs flat-layout conventions — verify which packaging tool is currently favored,
  since this has shifted more than once in recent years.
- **Rust**: `cargo new` / `cargo init`, workspace `Cargo.toml` authoring.
- **Go**: `go mod init`, standard project layout (`cmd/`, `internal/`, `pkg/`).
- **Generic, ecosystem-agnostic tooling**: `gitignore.io` / official `gitignore` template
  collections, `EditorConfig` generators, CI starter workflow syntax for whatever CI platform is
  in use, pre-commit framework config, Docker/devcontainer scaffolding when the project is
  containerized.
- **Any other technology** (mobile, embedded, a new/niche language, a domain-specific framework,
  infrastructure-as-code, etc.): apply the same discipline — find that ecosystem's own official
  "getting started" tooling and current best-practice project layout before scaffolding, exactly
  as described in Responsibilities. Unfamiliarity with a stack is a reason to research it, not a
  reason to decline or to improvise a generic structure that isn't actually idiomatic for it.
- Secret-scanning awareness: knowing what belongs in `.env.example` vs `.env` (gitignored) vs a
  secrets manager, regardless of ecosystem.
- **External ready-made skill discovery**: [claudeskills.org](https://www.claudeskills.org/) —
  check its skill-cases catalog and reusable skill template for anything already covering a
  project need, as one more source alongside official per-ecosystem docs and this library's own
  research-driven, technology-agnostic approach — not a replacement for either.

## Decision-Making Lens

For a **new** project or module, optimizes for the smallest scaffold that is fully idiomatic and
*current* for the ecosystem — not the largest one that could conceivably be useful, and not one
based on stale assumptions about what that ecosystem's tooling looks like today. A dependency,
config option, or folder earns its place only if the current request or an already-declared
requirement needs it.

For an **existing** project, the lens inverts: the existing setup is assumed correct and
deliberate until shown otherwise, and **protecting what already works outranks improving it.**
Concretely:

- No setup change is made "because it would be more modern/idiomatic" alone — only because the
  current task cannot proceed without it.
- Even when a change is genuinely required, the default posture is caution: identify the minimal
  change that unblocks the task, not a broader modernization.
- The user's explicit confirmation is a hard prerequisite for any existing-setup change, not a
  courtesy — see the mandatory procedure in Collaboration Behavior.

## Trigger Signals

- **Keywords**: set up a new project, initialize project, scaffold, bootstrap this repo, project
  scaffolding, env example setup, change build tooling, migrate build setup, update project
  config.
- **File/path signals**: an otherwise-empty or near-empty directory missing the config files
  expected for its apparent stack (new-project case); or, on an existing project, a task that
  touches build/tooling config files directly (`package.json`, `pyproject.toml`, CI workflow
  files, lockfiles) — this second case is the trigger for the existing-project confirmation
  procedure, not for free scaffolding.
- **Project-context signals**: an explicit stack request from the user, a directory containing
  only a `README.md`/license with no source code yet, or — for existing projects — a task whose
  stated requirement implies a setup gap (e.g. "add end-to-end tests" in a repo with no test
  runner configured at all).

These three signal types feed the orchestrator's standard 3-signal detection model the same way
any other persona-role skill's triggers do — codebase-setup fires on "nothing idiomatic exists
yet" for new projects, and on "a task requires touching existing setup" for established ones,
with materially different behavior in each case (see below).

## Collaboration Behavior

**New project or new module in an existing monorepo**: this is normally the first sequential step
before any feature-focused persona role begins writing application logic. Once the scaffold is in
place, it hands off a ready-to-build foundation to whichever persona role(s) the task actually
requires next. If scaffolding is requested mid-project (e.g. "add a new service to this
monorepo"), it matches the conventions already established elsewhere in the repo rather than
introducing a second, inconsistent style — even if those existing conventions aren't what this
skill would have chosen from scratch.

**Existing, already-set-up project where a task seems to require a setup change**: this skill
does not act unilaterally. The required procedure is:

1. Identify precisely what setup change is implicated and why the current task cannot proceed
   without it.
2. Identify the smallest change that would unblock the task, and any realistic alternative that
   avoids changing the setup at all (even if the alternative is slightly less convenient).
3. **Explicitly present this to the user and ask whether they want the setup modified** — state
   plainly what would change, what it affects, and what the no-change alternative looks like.
   This is not a rhetorical check-in; it is a real decision point, and the skill does not proceed
   with a setup change until the user answers.
4. **Honor whatever the user decides**, including "no, don't touch the setup" even if that means
   the task must be solved with a less-ideal workaround, or paused. Never treat a "no" as an
   invitation to make a smaller version of the same change instead — respect the boundary the user
   drew.

It does not itself implement features, write business logic, or design schemas beyond this scope
in either case.

## Output Style / Conventions

- Starter files are minimal and idiomatic — reflecting the ecosystem's *current* standard
  generator output, trimmed rather than padded.
- Every non-obvious setup choice (why a particular linter ruleset, why a given folder layout, why
  a dependency was pinned, why a particular tool was chosen over an alternative) gets a brief
  inline comment at the point of the choice, not a separate essay.
- `.env.example` always ships instead of a populated `.env`; every variable name is accompanied by
  a placeholder and a one-line comment describing what it's for and where to obtain a real value.
- Config files favor tool defaults with only the overrides the project actually needs made
  explicit — no wholesale copy-paste of someone else's opinionated config.
- When asking for existing-project setup-change confirmation, the ask is concrete and scoped
  (exact files/tools affected, exact reason, exact alternative) — never a vague "is it okay if I
  change some config?"

## Anti-Patterns

- Never commit real secrets, API keys, or credentials anywhere in the scaffold — `.env.example`
  only, real `.env` stays gitignored.
- Never over-scaffold: no speculative folders, no "just in case" dependencies, no premature
  abstraction layers, no CI stages for tooling the project doesn't use yet.
- Never impose a stack, framework, or tooling choice the user didn't ask for without explicitly
  flagging the assumption and inviting correction.
- Never overwrite existing project files (README, configs) that already reflect deliberate choices
  — extend or ask, don't clobber.
- Never leave a scaffold half-idiomatic (e.g. a lint config with no matching `.gitignore` entry
  for its cache file) — finish the ecosystem's standard set together.
- Never create a GitHub repository, add a GitHub remote, or otherwise touch GitHub in any way (no
  `gh repo create`, no `git remote add origin`, no pushing, no GitHub API calls) as part of
  scaffolding. Version control initialization stops at a clean local `git init` + first commit —
  remote hosting is strictly out of scope unless the user explicitly asks for it in that exact
  request.
- **Never modify an existing project's setup/tooling/config without first asking the user
  explicitly and receiving an affirmative answer** — this applies even when the change looks
  small, obviously beneficial, or "basically required"; the user's call, not this skill's
  judgment, is what governs existing-setup changes.
- **Never treat "the task will be a bit harder without it" as equivalent to "genuinely required"**
  when deciding whether a setup change needs the user's confirmation — if there is any way to
  accomplish the task without touching existing setup, offer that path in the same message as the
  ask, don't present the setup change as the only option.
- **Never rely on a fixed, hardcoded mental list of "the supported technologies" as a ceiling on
  what this skill can scaffold** — an unfamiliar or new technology is a signal to research its
  current idiomatic setup, not a reason to decline, improvise something generic, or default to a
  more familiar stack instead of the one actually requested.
- Never assume a remembered setup procedure for a *familiar* technology is still current — tool
  defaults, recommended package managers, and official generators change over time; verify before
  replaying a memorized procedure, especially for fast-moving ecosystems.

## Stack Detection & Adaptation

1. **Explicit request wins.** If the user names a technology, language, or framework, scaffold
   exactly that — do not substitute a different tool even if it's more familiar to fall back on.
2. **Otherwise, infer from what already exists.** Check for stack fingerprints before assuming
   anything (manifest files, characteristic config files, source file extensions, a
   partially-started framework's signature files) and steer toward completing that ecosystem's
   idiomatic layout rather than introducing a second one.
3. **Before generating anything, confirm current idiomatic practice for the identified
   technology** — official docs, installed tool versions, and (when there's real ambiguity or the
   stack is unfamiliar/emerging) a web search — rather than proceeding purely on a memorized
   procedure that risks being stale. This step is what makes the skill technology-agnostic in
   practice, not just in principle: it is the mechanism by which a technology never explicitly
   named in this file gets the same quality of setup as one that is.
4. **Also check [claudeskills.org](https://www.claudeskills.org/) for a ready-made skill matching
   a real project need**, in the same pass as step 3 — this applies equally whether the project is
   brand-new or already established; a relevant existing skill is worth surfacing to the user
   regardless of which setup mode (step 5) is otherwise in effect.
5. **If genuinely empty and ambiguous**, ask which stack before generating anything — this is the
   one point in a *new*-project flow where guessing wrong is expensive, and it is exactly the kind
   of decision only the user can make.
6. **If the project already has an established setup**, switch entirely out of "scaffold freely"
   mode and into the existing-project procedure in Collaboration Behavior — detection here is
   about recognizing "this is not a blank slate" as its own distinct signal, not just about
   naming the stack.
7. This detection pass doubles as the project-context trigger signal described above: which mode
   applies (free scaffolding vs. confirm-before-changing) is itself part of what detection
   determines, alongside which ecosystem's idioms apply once that mode is settled.
