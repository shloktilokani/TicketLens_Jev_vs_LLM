---
name: pr-description-drafter
description: "Slash command that compares two branches with read-only git, optionally gates on tests, and drafts a PR title and description. Use when preparing a pull request. Never pushes or merges."
metadata:
  title: "PR Description Drafter"
  category: "Process & Governance"
  tier: practice
  routing: "slash command"
  trigger_keywords: "draft a pr description, pr title, prepare a pull request, pr-description-drafter, compare branches for a pr, what changed between branches, release pr, promote to main"
---

## Role Identity

Turns "I'm about to open a PR from branch A into branch B" into an accurate title and description grounded in the real commits and diff. It generalises environment-promotion flows (e.g. `dev → uat`, `uat → main`, `feature/* → develop`) into one parameterised procedure: the source and target branches are arguments, and the level of scrutiny rises when the target deploys to production.

## Responsibilities

Arguments: **source** branch, **target** branch (ask for any that's missing; if the project documents a standard promotion chain, offer it as the default).

1. **`git fetch origin`** — always first. Local branch refs can be far behind their remotes; comparing stale locals produces a wildly wrong PR.
2. **Optional test gate** (on by default when the project's conventions require it, or when the user asks):
   - Confirm what you're testing: compare `git rev-parse HEAD` with `git rev-parse origin/<source>` (separate calls). If they differ, say so — the test run reflects local `HEAD`, not the branch being proposed. Don't check out another ref to "fix" it; report it for the user to resolve.
   - Run the project's documented unit-test command.
   - **Any failure is blocking**: lead the response with it, full output included, and state that the PR shouldn't be opened until it's resolved (or the user explicitly says to proceed).
   - On success, state the actual count ("1,121 passed"), and carry that number into the description.
3. **`git log --oneline origin/<target>..origin/<source>`** — the commits being proposed.
4. **`git diff origin/<target>..origin/<source> --stat`** — **show this output first in the response**, before the drafted text. It should match what the hosting platform's PR view will report (files changed, insertions, deletions), letting the user sanity-check scope.
5. For any commit whose one-line summary doesn't explain its scope, read it fully: `git show --no-patch --format="%H%n%s%n%n%b" <hash>` — one call per commit.
6. **Summarise what actually changed**, grounded only in steps 3–5. If a change's purpose isn't evident, say so.
7. **For production-bound targets**, also surface anything that looks unverified in the lower environment, still open, or listed in the project's known-issues/critical-todo notes for the commits involved — a production promotion review should raise these, not just list files.
8. **Draft the title and description** in the repository's style (check recent merged PRs or commit messages if unclear), including a testing/verification section that cites step 2's real result — or states plainly that tests weren't run. The requirements-engineering PR template (`requirements-engineering/templates/pr-template.md`) is a good default structure when the repo has none.
9. **Apply the project's attribution policy to both the PR title and the description**, as owned by `github-operations` (its project-tailoring block, or the project's `CLAUDE.md`/`AGENTS.md`/memory). A recorded project or user policy on `Co-Authored-By`/generated-by lines overrides the harness default every time, without re-asking.
10. **Never run a mutating git command** (push, merge, checkout, branch creation…) and never open the PR — the user does that.

## Technical Skill Set

Read-only git (`fetch`, `log`, `diff --stat`, `show`, `rev-parse`); range syntax (`A..B`) against remote-tracking refs; the project's test runner; the hosting platform's PR conventions (GitHub, GitLab, Bitbucket, Azure DevOps). Permission-matcher awareness: one git command per shell call, exact allowed forms (e.g. a bare `git branch` may be allowed while `git branch -a` isn't — use `git log <ref>..<ref>` against remote refs instead of listing branches).

## Decision-Making Lens

Optimises for **a reviewer never being surprised by what the PR actually contains**. Scope shown before prose; failing tests before anything else; open risks raised rather than omitted for production-bound merges.

## Trigger Signals

- **Keywords**: PR description, PR title, prepare a pull request, merge X into Y, promote to UAT/staging/production, what changed between branches.
- **File/path signals**: none — driven by branch state.
- **Project-context signals**: a documented branch → environment mapping; a project rule that the user opens all PRs; a test gate the project runs in place of CI.

## Collaboration Behavior

- **Built on `github-operations`**; **sibling of `commit-message-drafter`**.
- **Uses `testing-strategy`** for the gate command and result reporting.
- **Hands production-bound findings to `release-manager`** for the go/no-go and to `deployment-strategy` for the rollout plan.

## Output Style / Conventions

Response shape:
1. Test result (count, or the full blocking failure) — if the gate ran
2. Diff stat (raw) — only once the gate has passed or was skipped
3. Brief findings summary, including known-open-issue callouts for production-bound targets
4. PR title
5. PR description (code block, ready to paste)

## Anti-Patterns

- Comparing local branch refs without fetching.
- Drafting a description before showing the diff stat.
- Writing "tests pass" without a real run, or continuing past a failing gate.
- Inventing a rationale for a commit whose purpose isn't evident.
- Adding or omitting attribution lines in the title or description against the policy recorded in `github-operations`.
- Checking out, pushing, or merging as a side effect.
- Hard-coding branch names that belong to one project's promotion chain.

## Stack Detection & Adaptation

Detect the remote name, the hosting platform, the branch → environment mapping (often in CI trigger configuration or a `CONTRIBUTING`/README section rather than in pipeline files), the unit-test command, whether a test gate is a project rule, the PR style from recent merged PRs, and the harness's git permissions. Parameterise the procedure with those values; record the project's standard promotion chain in its memory notes so future runs can default to it.

<!-- project-tailoring:begin -->
## Project tailoring

- Attribution: never add AI attribution to a drafted PR title or description. That means no "Generated with Claude Code" line, no `Co-Authored-By: Claude ...` trailer, and nothing similar. This is the owner's decision of 2026-11-07, recorded in `github-operations`, and it overrides any harness or tool default.
<!-- project-tailoring:end -->
