# UI Automation Mechanics

Technical grounding for driving a user-facing app like a real user. The SOP in `../SKILL.md` is
the procedure; this file is the mechanics it relies on.

## 1. Read the real source before trusting selectors

The UI under test may live in a different repository from the backend. Read its actual markup
and scripts before writing selectors — front ends change often, and any selector table is a
point-in-time snapshot. Record verified selectors (with the date verified) in the project's
tailoring notes:

| Element | Selector | Notes |
|---|---|---|
| Launcher / entry point | `#…` | Click first if the feature is behind a toggle |
| Input field | `#…` | |
| Submit control | `#…` | Enter in the input is often a reliable fallback |
| One turn / result container | `.…` | The unit to screenshot |
| In-flight indicator | `.…` | Appears on submit, removed when the response lands |

Prefer stable IDs and data attributes. Elements without ARIA roles won't appear in
accessibility-tree snapshots — target them by CSS selector.

## 2. Layered wait strategy — never one blind sleep

Many renderers draw *after* the response arrives (charting libraries paint after their
container exists). Wait in layers:

1. The in-flight indicator is detached (the round trip finished).
2. The new result container is visible.
3. For rich content, the rendered artefact itself exists inside it (e.g. the chart's root
   `<svg>` or a series element) — container presence alone isn't proof the draw finished.
4. A short, explicit settle buffer (~1–2 s) for CSS transitions — the one deliberately
   approximate step, kept short and visible.

If a response is taking unusually long, check the backend's run record (many systems write a row
the moment a request starts) to distinguish "still processing" from "stuck."

## 3. Know which response type rendered

If the UI renders different response types (chart, table, text, multi-part…), record which one
actually appeared — preferably by intercepting the network response in the browser tool, which
is more reliable than inferring from DOM shape. Don't assume every input produces the same type.

## 4. Embedding gotcha: theme leakage in charting libraries

Some charting libraries inject their own `color-scheme` or theme rules into their container at
render time. When embedding a chart in a page other than the app's own (a replay/debug view, a
report), a dark-mode OS can wash out chart text unless the container itself forces the intended
scheme (e.g. `color-scheme: light !important` on the chart container — a page-level setting may
lose the cascade to the library's later-injected rule).

## 5. Output conventions

Follow the repository's existing batch-output pattern if it has one (one folder per run,
timestamp-named, one file per input). Otherwise:

```
<ui-testing-root>/<env>/<YYYYMMDD_HHMMSS>/
├── manifest.json          # plan + outcomes: input, persona, category, origin, response type, status, run id
├── results.ctrf.json      # optional: CTRF for dashboards
├── results.junit.xml      # optional: CI-compatible sibling
├── failures.jsonl         # one JSON object per failure
├── q001_<slug>.png
├── q002_<slug>_FAILED.png
├── traces/                # optional, failures only
└── report.md
```

Screenshots and traces are binary run artefacts that may contain real data — git-ignore them.
Commit only a README or summary for a run worth keeping.

## 6. Credential handling — no plaintext anywhere

Browser automation has more leak surfaces than a backend script: screenshots, traces, and videos
capture DOM and visual state that plain logs never would.

- **Storage**: the OS credential manager (e.g. Python `keyring` → Windows Credential Manager /
  macOS Keychain / Secret Service), never a plaintext file — not even a git-ignored one. One small
  module is the only code that reads the credential; it hands the value straight to the one
  browser call that needs it and never logs, returns, or stores it.
- **Login step**: tracing and video **off** while credentials are entered (traces store full DOM
  snapshots, which capture typed values even when the screen masks them); mask the relevant
  regions in any screenshot taken during login.
- **Session reuse**: after one login, save the browser's storage state and reuse it within its
  validity window so the typed-credential step happens as rarely as possible. **Treat that saved
  state file as a secret** — git-ignored, ideally stored outside the repo (OS user-profile app-data).
- **No credentials in command-line arguments, environment dumps, or long-lived subprocess
  environments** — visible in shell history and process lists.
- **Dedicated, revocable, low-privilege test account** — never a real employee's identity.
- **Redact before writing** any log, manifest, or error message to disk.

## 7. Decisions to get from the owner, not guess

- Which login path automation may use (test account, dev bypass, SSO).
- Target environment (local / staging / production).
- How synthetic traffic is tagged (a `source`/test-user convention) so it doesn't pollute real
  usage analytics.
