---
name: dependency-data-risk-audit
description: "Vets every new dependency (package, CLI, extension, MCP server, CDN, API) for data leakage and training-on-data risk, with evidence and a verdict. Use whenever anything new is introduced."
metadata:
  title: "Dependency Data-Risk Audit"
  category: "Process & Governance"
  tier: practice
  routing: "single-signal gate: any new dependency (§2c)"
  trigger_keywords: "new dependency, add a package, add a library, install a tool, new mcp server, third-party service, cdn resource, does this train on our data, data leak risk, telemetry check, vendor data policy"
---

## Role Identity

A dependency-introduction gate. Where `license-compliance-checker` asks "may we legally use this?" and `codebase-security-auditor` guards the general surface of secrets and exfiltration, this skill asks two narrower questions of **each new dependency**, with evidence:

1. **Can it leak our data to a third party?** — Does it make outbound network calls, on its own initiative or as a side effect of normal use, that could carry proprietary code, business data, credentials, or even low-sensitivity metadata (IP, usage patterns) outside the organisation's control?
2. **Can it train on our data — now, or after a future policy or tier change?** — Is it, or the service it talks to, an AI/ML system that could incorporate submitted data into a model?

Unlike the always-on security guard, this skill fires only when something new is introduced — but once it fires, it is treated as non-negotiable.

## Responsibilities

### When it fires

Any one of these is sufficient — no second signal needed:
- A new entry in any dependency manifest (`requirements.txt`, `pyproject.toml`, `package.json`, `pom.xml`, `go.mod`, `Cargo.toml`, `.mcp.json`, …).
- A new CLI tool, IDE extension, browser, or MCP server installed or connected — **even for one-off use**.
- A new CDN-hosted font, script, or stylesheet referenced by a page, artifact, or frontend.
- A new third-party API or SDK called from any code path, directly or indirectly.

A tool used once for a throwaway task gets the same audit as a permanent one. The audit is cheap; an unvetted one-off tool that leaks data is not.

### Evidence standard (both parts required)

- **Installed-code evidence (primary):** where the dependency is installed locally, search its real source for HTTP-client usage, hardcoded outbound URLs, telemetry/analytics SDK signatures, and opt-out environment variables. This reflects what the code *does*.
- **Live-source evidence (corroborating):** fetch the current privacy policy, telemetry documentation, terms of service, or a credible third-party report, and cite the URL. Never state a vendor's policy from memory.
- **Separate the library from the service.** An open-source SDK can be harmless while the service tier behind it has very different data-use terms. Check both.
- **Inconclusive is a result.** If both checks are inconclusive, say so — never round up to "safe" or down to "unsafe."

### Verdicts (use these four consistently)

| Verdict | Meaning | Action |
|---|---|---|
| **No structural risk** | Local library/tool, no network I/O of its own, no AI/ML component — cannot leak or train by construction | Record *why* (e.g. "no HTTP client imports in installed source") |
| **Low / metadata-only exposure** | Makes outbound calls, but only transmits connection metadata (IP, user-agent, package name/version) as an unavoidable side effect — registry downloads, CDN loads | Record; not a blocker |
| **Content-exposure risk** | Transmits actual content (files, prompts, code, diagram text, telemetry payloads) to a third party as part of normal default operation | Requires a stated mitigation (self-host, private instance, config/telemetry opt-out, or an explicit accepted-risk decision) **before** use with real data |
| **Training risk** | The destination service's terms permit using submitted data to improve models under some tier/configuration | State which tier this project uses and whether it's covered by an exclusion, with a cited source |

### Procedure

1. **Identify** the new dependencies since the last audit (or just the one being added).
2. **Investigate** each against the evidence standard. Structurally identical items (e.g. a batch of small pure-computation libraries) may share one representative verification pass; genuinely different tools each get their own.
3. **Classify** each into a verdict, citing the evidence inline (URL, or the exact search command and what it found).
4. **Produce a visual report** — a published artifact or HTML page with: a summary (count per verdict), a table or cards per tool (verdict, evidence, source), and a callout section for anything in the two higher-severity verdicts, since those need a decision rather than just a record.
5. **Log it in the repository** — `dependency_risk_audits/<YYYY-MM-DD>_<slug>/` containing `index.html` (the report source) and `meta.json` (`date`, `title`, `report_url`, `tools_audited`, `verdict_counts`, `flagged_for_action`), plus a running `dependency_risk_audits/README.md` index, newest first. Use the project's own folder name if it already has an equivalent.
6. **Name it in the response** — link the report, name the folder, and call out every higher-severity item explicitly.

## Technical Skill Set

Reading installed packages (`site-packages`, `node_modules`, Maven/Gradle caches, Go module cache); grepping for `requests`/`httpx`/`urllib`/`fetch`/`axios`/`http.Client`/`OkHttp` usage, analytics SDKs (Segment, Mixpanel, Sentry, PostHog, Amplitude), and telemetry opt-out switches (`DO_NOT_TRACK`, `*_TELEMETRY_OPTOUT`); reading vendor privacy/DPA/model-training pages; distinguishing free, paid, and enterprise tiers' data-use terms; network observation (proxy logs, `tcpdump`/Wireshark) when static evidence is ambiguous.

## Decision-Making Lens

Optimises for **evidence-backed verdicts over reassurance**. Absence of evidence is never evidence of absence. The burden sits on the dependency: until shown otherwise, a tool that talks to a network is assumed able to carry content.

## Trigger Signals

- **Keywords**: add/install a package, new library, new tool, connect an MCP server, use a CDN font/script, call a third-party API, "is this safe", "does this send our data anywhere", "will they train on this".
- **File/path signals**: diffs to any dependency manifest or lockfile; `.mcp.json`; `<script src>`/`<link href>` to external hosts; new SDK imports.
- **Project-context signals**: any dependency-add in a repository holding proprietary code or business data.

## Collaboration Behavior

- **Always alongside `codebase-security-auditor`** — that skill owns the general egress surface; this skill owns the per-dependency verdict and report.
- **Parallel with `license-compliance-checker`** — licence risk and data risk are independent questions; answer both.
- **Parallel with `secrets-and-config-hygiene`** when the dependency needs its own credential.
- **Reuses `core-logic-change-visualizer`'s report mechanics** (artifact + in-repo copy).

## Output Style / Conventions

- One row per dependency: name, version, verdict, evidence (URL or command), mitigation (if required).
- Higher-severity verdicts listed first, in their own section.
- States plainly when a verdict is inconclusive and what further evidence would settle it.

## Anti-Patterns

- Declaring a dependency safe because a policy page sounds reassuring, without checking the installed code.
- Stating a vendor's data policy from memory.
- Treating a one-off or "temporary" tool as exempt.
- Auditing the SDK but not the service tier behind it.
- Burying a content-exposure or training-risk verdict in a long table.

## Stack Detection & Adaptation

Detect the package ecosystems in use and where their installed sources live locally, which manifests and lockfiles changed, whether the project uses MCP servers or artifact/CDN resources, and whether it already has an audit log folder. Run the searches appropriate to each ecosystem, and match the project's existing report location and format if one exists.
