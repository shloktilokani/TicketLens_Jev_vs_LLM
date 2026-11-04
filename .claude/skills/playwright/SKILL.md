---
name: playwright
description: "Deep reference for the Playwright test framework: locators, auto-waiting, fixtures, config, tracing, mocking, API/component tests, CI. Use when writing or debugging Playwright tests."
metadata:
  title: "Playwright"
  category: "Quality"
  tier: supporting
  routing: "conditional: only if the project uses Playwright"
  trigger_keywords: "playwright test runner, playwright locator strategy, playwright trace viewer, playwright codegen, playwright fixture setup, playwright component testing, playwright config setup"
---

## Role Identity

This is a **supporting/technical-reference skill**, not a persona and not usually a task's
primary entry point — the same category as `agent-browser`. Where `test-automation-engineer`
owns test *methodology* (what to test, how to record results, which target type) and
`agent-browser` is a separate, independent browser-automation tool (a native Rust CLI using CDP
directly with **no Playwright dependency**), this skill is the deep, concrete reference for
**Playwright itself** — its actual API surface, config model, and tooling — grounded in the
current official documentation (playwright.dev, current release **1.62**: Chromium 151, Firefox
153, WebKit 26.5) rather than a possibly-stale memorized snapshot. Playwright ships frequently and
has materially changed shape even recently (a new component-testing model replacing the old
`experimental-ct-*` packages in 1.62; an explicit CLI/MCP surface aimed at AI coding agents) — this
skill's job is to keep delegating skills current against that reality, not to freeze a point-in-
time understanding.

## Responsibilities

- **Recommend the right locator strategy, in priority order**: `getByRole()` (ARIA role +
  accessible name — the recommended default, W3C-aligned) first, then `getByText()`/`getByLabel()`/
  `getByPlaceholder()`/`getByAltText()`/`getByTitle()`/`getByTestId()`; raw CSS/XPath
  `page.locator()` selectors are a last resort, not a starting point, because they're brittle
  against markup churn. Locators are **strict** by default (throw on >1 match) — disambiguate with
  `.filter()`, `.and()`/`.or()`, or `.first()`/`.last()`/`.nth()` used deliberately, not reflexively.
- **Lean on the auto-wait/auto-retry model rather than manual waits.** Every action
  (`click`/`fill`/`check`/etc.) passes actionability checks (visible, stable, enabled, receives
  events) before firing; web-first assertions (`toBeVisible`, `toHaveText`, etc. on `Locator`) retry
  automatically until they pass or time out. Recommend these over `page.waitForTimeout()` or
  polling loops, which are exactly the anti-pattern this model exists to replace.
- **Set up config, parallelism, retries, and sharding correctly**: `playwright.config.ts` via
  `defineConfig()` — `testDir`, `timeout`, `fullyParallel`, `workers`, `retries`, `reporter`,
  `projects` (multi-browser/device/environment runs, chainable via `dependencies` for e.g. an
  auth-setup project), `webServer` (auto-start a dev server before tests), and the `use` block
  (`baseURL`, `trace`, `screenshot`, `video`). Distinguish `retries` (config-level flakiness
  tolerance, surfaces as passed/flaky/failed) from `test.describe.configure({mode: 'serial'})`
  (dependent-test groups). For CI at scale, set up `--shard=N/M` with a `blob` reporter per shard
  and `npx playwright merge-reports` to combine.
- **Build fixtures and Page Object Models correctly**: built-in fixtures (`page`, `context`,
  `browser`, `browserName`, `request`) and custom ones via `test.extend()`, choosing test-scoped
  vs. `{scope: 'worker'}` (shared/expensive setup) and `{auto: true}` (runs without being
  requested) deliberately rather than defaulting every fixture to test-scoped. POMs wrap a `Page`
  in a helper class exposing locators as properties and actions as methods — a plain design
  pattern, not a special API.
- **Point to the right debugging tool for the situation**: Trace Viewer (`trace: 'on-first-retry'`
  or similar in config, `npx playwright show-trace` to inspect — captures DOM snapshots, network,
  console, timings entirely locally, no upload required) for post-hoc failure investigation; UI
  Mode (`npx playwright test --ui`) for interactive watch-mode development with a time-travel
  timeline and locator playground; the VS Code extension for inline run/debug with breakpoints;
  `--debug`/Playwright Inspector or `page.pause()` for step-through debugging live.
- **Set up network mocking/interception and auth correctly**: `page.route()`/`context.route()`
  with `route.fulfill()`/`route.continue()`/`route.abort()` for request interception;
  `page.routeFromHAR()` to replay recorded traffic. For auth, prefer API-based login via the
  `request` fixture over scripting a UI login flow (faster, less flaky), then persist via
  `storageState()` — a one-time "setup" project other projects depend on — rather than logging in
  fresh in every test.
- **Cover screenshots, video, and visual regression correctly**: `expect(page).toHaveScreenshot()`
  auto-generates and compares baselines (environment-sensitive — OS/browser/HW all affect pixel
  output, so baselines must be generated and compared in the same environment); `maxDiffPixels`/
  `maxDiffPixelRatio` for tolerance; `--update-snapshots` to intentionally refresh baselines.
- **Recommend API testing via the `request` fixture** (`APIRequestContext`) for pure-HTTP
  validation with no browser involved — seeding state before a UI test, verifying postconditions
  after one, or testing a REST API directly — distinct from `api-test-specialist`'s broader
  contract/schema-validation methodology, which may use this as its concrete execution tool.
- **Recommend the current component-testing model** (`npx playwright init-skills`, framework-
  agnostic — React/Vue/Svelte/Solid/anything a dev server can render — `mount()` returns a real
  `Locator` against a real browser) rather than the deprecated `@playwright/experimental-ct-*`
  packages, and flag explicitly if a project is still on the old model that it should migrate.
- **Set up CI/Docker correctly**: standard recipe (checkout → setup-node → `npm ci` →
  `npx playwright install --with-deps` → `npx playwright test`); the official Docker image
  (`mcr.microsoft.com/playwright:v1.62.0-noble`) requires glibc (**no Alpine/musl support** —
  browsers won't run) and should be run with `--ipc=host` to avoid Chromium OOM crashes; caching
  browser binaries in CI is explicitly not recommended by Playwright itself (restore time ≈
  download time).
- **Recommend accessibility-testing integration** via `@axe-core/playwright`'s `AxeBuilder`
  (`.withTags(['wcag2a','wcag2aa',...])`, `.include()`/`.exclude()`) as the automated-scan layer,
  paired with native ARIA-snapshot assertions (`toMatchAriaSnapshot()`, `toHaveAccessibleName()`)
  for structural checks — and explicitly repeat Playwright's own caveat (also true of
  `accessibility-specialist`'s broader stance) that automated scans catch only some issues and
  must be paired with manual/assistive-tech verification.

## Technical Skill Set

- **Install/scaffold**: `npm init playwright@latest` (also yarn/pnpm variants); scaffolds
  `playwright.config.ts` and an example spec, adds `@playwright/test`.
- **Two API layers**: `@playwright/test` (the recommended full framework — parallelism, fixtures,
  tracing, reporters built in) vs. the lower-level `playwright` Library package (manual
  `chromium.launch()`/`browser.newContext()`, no auto-retrying assertions) — recommend the former
  unless there's a specific reason to script outside the test runner.
- **Core CLI commands**: `npx playwright test` (+ `--headed`, `--ui`, `--debug`, `--project`,
  `-g/--grep`, `--shard`, `--repeat-each`, `-u/--update-snapshots`, `--trace`, `--last-failed`),
  `npx playwright codegen <url>` (records actions into code, auto-picks role/text/testid locators;
  supports `--device`, `--viewport-size`, `--save-storage`/`--load-storage` for recording
  authenticated flows), `npx playwright show-trace`, `npx playwright show-report`,
  `npx playwright install [--with-deps]`, `npx playwright merge-reports`.
- **Reporters**: `list` (default local), `line`, `dot` (default CI), `html` (self-contained,
  auto-opens on failure), `blob` (shard-merge fidelity), `json`, `junit`, `github` (inline Actions
  annotations); custom reporters implement `onBegin`/`onTestBegin`/`onTestEnd`/`onEnd`.
  `test.step()` for structured step reporting inside a test.
- **Engines/channels**: Chromium/Firefox/WebKit (Playwright's own builds, not branded
  Chrome/Safari/Firefox binaries) plus branded channels (`chrome`, `msedge`, and their
  beta/dev/canary variants) when testing against a specific real browser matters.
- **Language bindings**: JS/TS (`@playwright/test`, native test runner), Python
  (`playwright-python`, pytest plugin), Java (`playwright-java`, JUnit/TestNG), .NET
  (`playwright-dotnet`, MSTest/NUnit/xUnit) — the core browser-automation API is consistent across
  all four; test-runner ergonomics differ per ecosystem, so detect which one a project actually
  uses before recommending idioms.
- **Emerging surface worth knowing about, not necessarily the default recommendation**: a
  standalone Playwright CLI (`/docs/agent-cli/*`) and an MCP server (`/docs/mcp/*`) explicitly
  built for AI coding agents — accessibility-snapshot-based control rather than screenshot-based.
  This overlaps conceptually with `agent-browser`'s territory; when both are available in an
  environment, note the overlap explicitly rather than silently picking one.

## Decision-Making Lens

Optimizes for **resilience over cleverness in locator/wait strategy** — a `getByRole()` locator
that survives a markup refactor beats a CSS selector that's marginally shorter to write today.
Optimizes for **using the framework's built-in retry/isolation mechanisms** (auto-waiting
actions, auto-retrying assertions, per-test `BrowserContext` isolation, `retries`/flaky-detection)
over hand-rolled equivalents (manual sleeps, shared global state, custom retry loops) — Playwright
built these because the naive versions are exactly what causes flaky suites. Optimizes for
**verifying current API/config shape against the actual installed version and current docs**
before recommending something, since Playwright's own capability surface has changed meaningfully
even in recent minor versions (the 1.62 component-testing model replacing the old
`experimental-ct-*` packages is the clearest recent example) — a recommendation grounded in a
stale snapshot can actively point a project at a deprecated approach.

## Trigger Signals

- **Keywords**: Playwright test runner, Playwright locator strategy, Playwright trace viewer,
  Playwright codegen, Playwright fixture setup, Playwright component testing, Playwright config
  setup.
- **File/path signals**: `playwright.config.ts`/`.js`, `*.spec.ts`/`*.spec.js` test files,
  `tests/`/`e2e/` directories, `playwright-report/`, `test-results/`, `*.story.tsx` (component
  testing), an existing `@playwright/test` dependency in the manifest.
- **The primary trigger path is indirect**, like `agent-browser`: this skill is most often
  invoked *by* `test-automation-engineer`'s Collaboration Behavior when it needs concrete
  Playwright implementation detail, rather than triggering directly on a raw user request — a
  request like "write an end-to-end test for the checkout flow" routes through
  `test-automation-engineer` for methodology, which delegates here for the actual Playwright API/
  config specifics.
- **Project-context signal**: the detected stack already uses Playwright (per the file/path
  signals above), or a task explicitly names Playwright rather than describing a generic
  "automate the browser" need (which could route to `agent-browser` instead or in addition).

## Collaboration Behavior

- **`test-automation-engineer`** is the primary delegator — it owns test methodology, input
  fixtures, and result-recording format (CTRF/JUnit), and delegates here for the concrete
  Playwright API/config/tooling needed to actually implement a web-UI test session (this skill's
  Technical Skill Set is the same content already cross-referenced from that skill's own).
- **`api-test-specialist`** may delegate here for the `request` fixture / `APIRequestContext` as
  a concrete execution tool for API-level test suites, distinct from that skill's own broader
  contract/schema-validation methodology.
- **`accessibility-specialist`** delegates here for `@axe-core/playwright` integration and native
  ARIA-snapshot assertions as the automated-scan layer within its broader manual+automated
  verification approach.
- **`qa-test-engineer`** delegates here when exploratory or regression testing needs an actual
  Playwright script rather than a manual walkthrough.
- **Sibling relationship with `agent-browser`**: both can drive a real browser, but they are
  different tools with different tradeoffs (Playwright: full test-runner framework, deep
  assertion/fixture/reporting ecosystem, requires writing/maintaining test code; Agent Browser:
  native Rust CLI, no Playwright dependency, accessibility-tree `@eN` refs, built for direct
  agent-driven interaction rather than authored test suites, plus Electron/Slack support
  Playwright doesn't have). When a task could go either way, state the tradeoff rather than
  silently picking one — e.g. a one-off exploratory click-through favors `agent-browser`, a
  maintained regression suite favors Playwright.

## Output Style / Conventions

- Cites the actual current API/config field names and CLI flags (e.g. `fullyParallel`,
  `test.describe.configure({mode: 'serial'})`, `--shard=1/4`) rather than paraphrasing loosely —
  precision matters because config typos fail silently or behave unexpectedly.
- When recommending a locator or assertion, states *why* that one over an alternative (e.g. "use
  `getByRole` over a CSS class selector because the class name is a styling concern, not a stable
  contract") rather than issuing the recommendation as an unexplained rule.
- Flags version-sensitivity explicitly when a feature is new/recently changed (e.g. the 1.62
  component-testing model) so the reader knows to double check against the project's actual
  installed version rather than assuming universal applicability.

## Anti-Patterns

- Never recommend `page.waitForTimeout()` or manual polling loops as a fix for flakiness when the
  actual fix is using a proper auto-retrying locator/assertion — this papers over a real race
  condition rather than resolving it.
- Never default to CSS/XPath selectors when a role/text/label/testid locator would work — brittle
  selectors are a leading cause of test maintenance burden.
- Never recommend generating and comparing visual-regression baselines across different
  environments (e.g. baseline from a local Mac, compared in Linux CI) — baselines are
  environment-sensitive by design; mismatched environments produce false-positive diffs.
- Never recommend caching Playwright's browser binaries in CI — Playwright's own documentation
  states this isn't worth it (restore time ≈ download time, and Linux system deps don't cache
  well).
- Never recommend Alpine-based Docker images for running Playwright — browsers require glibc;
  Alpine's musl libc will not work.
- Never let credentials get baked into a committed `storageState`/auth file — treat it like any
  other secret (`.gitignore`d `playwright/.auth`, never committed) and coordinate with
  `codebase-security-auditor` on this specifically, since a leaked storage-state file is a leaked
  authenticated session.
- Never recommend a deprecated API (e.g. the old `@playwright/experimental-ct-*` component-testing
  packages) without flagging that a current alternative exists — verify against current docs
  before treating a memorized pattern as still correct.

## Stack Detection & Adaptation

1. Detect the installed Playwright version (`package.json`/lockfile, or `npx playwright
   --version`) and the language binding in use (JS/TS `@playwright/test`, Python
   `playwright-python`, Java `playwright-java`, .NET `playwright-dotnet`) before recommending
   syntax — core browser-automation concepts are consistent across bindings, but exact test-runner
   idioms differ.
2. Detect existing config (`playwright.config.*`) and existing test conventions (locator style
   already in use, existing fixtures, existing reporter setup) and extend those rather than
   imposing a different style — consistency with what's already there beats a "better" pattern
   introduced inconsistently.
3. Before recommending a specific feature or API shape, verify it against the current official
   documentation/release notes if there's any chance the memorized understanding could be stale —
   Playwright ships frequently enough that this is a real, recurring risk, not a hypothetical one.
4. This detection pass doubles as the project-context trigger signal above: an existing Playwright
   setup is itself the strongest signal this skill (rather than `agent-browser` or a from-scratch
   recommendation) is the right one to delegate to for that project's browser-automation needs.
