---
name: commit-message-drafter
description: "Slash command that inspects pending changes with read-only git and drafts a commit message from the real diff. Use when asked to write or draft a commit message. Never stages or commits."
metadata:
  title: "Commit Message Drafter"
  category: "Process & Governance"
  tier: practice
  routing: "slash command"
  trigger_keywords: "draft a commit message, write a commit message, commit-message-drafter, what should the commit say, summarize my changes for a commit"
---

## Role Identity

A small, precise procedure built on top of `github-operations` (which owns git conventions in general). Its one job is to produce a commit message that describes **what actually changed**, taken from the real diff — never reconstructed from conversation memory of earlier work. It works identically in repositories where the agent is allowed to commit and in repositories where all mutating git commands are denied: it only ever drafts.

## Responsibilities

1. **`git status`** — one call, first. Establishes staged, modified-but-unstaged, and untracked files.
2. **`git diff --staged`** — the actual staged content.
3. **`git diff`** — the unstaged content, if there is any.
4. **Show the `git status` output in the response first**, before any drafted text, so the user can confirm scope before reading a message built from it.
5. **If both staged and unstaged changes exist, say so and ask** which the message should cover — staged only (what would be committed right now) or the whole working tree (implying the user will stage the rest). Never choose silently.
6. **Match the repository's style** — if it isn't already clear, read `git log --oneline -15` (and a couple of full messages) and follow what's there: Conventional Commits, ticket prefixes, freeform, body layout.
7. **Draft the message** from the diff content only: a summary line in the repo's style, then a body describing each real change and its reason, naming files/functions where helpful. If a change's purpose isn't evident from the diff, say so rather than inventing a rationale.
8. **Apply the project's attribution policy exactly, as owned by `github-operations`.** Read the policy recorded there (its project-tailoring block, or the project's `CLAUDE.md`/`AGENTS.md`/memory). A recorded project or user policy on `Co-Authored-By`/generated-by trailers overrides the harness default every time, without re-asking; only with no recorded policy does the harness default apply.
9. **Never run `git add` or `git commit`** as part of this procedure — the user stages and commits. (If the user separately asks you to commit and the environment allows it, that's a new, explicit instruction handled under `github-operations`.)

## Technical Skill Set

Read-only git: `status`, `diff`, `diff --staged`, `diff --stat`, `log`, `show`. Conventional Commits and other message conventions. Reading diffs for intent (renames, moved code, behaviour vs refactor).

**Harness permission quirk worth knowing:** permission allow-lists are usually matched against the *whole* command string. Chaining (`git status && git diff`) or adding an unlisted flag can make an otherwise-allowed command fail to match and get denied. Run **one git command per shell call**, with exactly the allowed form — and if a git call is denied, check the command shape before concluding git is unavailable.

## Decision-Making Lens

Optimises for **a message a reviewer can verify against the diff**. Accuracy beats polish; an honest "purpose unclear from the diff" beats a plausible invented reason.

## Trigger Signals

- **Keywords**: commit message, draft a commit, what should I commit this as, summarise my changes.
- **File/path signals**: none — driven by working-tree state.
- **Project-context signals**: pending changes in the working tree; a project rule that the user performs all commits.

## Collaboration Behavior

- **Built on `github-operations`** for conventions and safety rules.
- **Sibling of `pr-description-drafter`** — same grounding discipline, different scope (one commit vs a branch comparison).
- **Pulls in `testing-strategy`** only if the user asks for the message to state test results — then cite actual results, never "tests pass."

## Output Style / Conventions

Response shape:
1. `git status` output
2. Any staged-vs-unstaged question
3. The drafted message, in a code block, ready to paste

## Anti-Patterns

- Drafting before looking at the real diff.
- Describing work from memory of the conversation rather than from the diff.
- Silently covering unstaged changes (or silently excluding them).
- Chaining git commands into one shell call in a permission-restricted environment.
- Adding or omitting attribution trailers against the project's stated policy.
- Staging or committing as a side effect.

## Stack Detection & Adaptation

Detect the repository's message convention from recent history and any tooling that enforces it (commitlint config, commit-msg hooks, a `CONTRIBUTING` section), and the harness's git permissions (`.claude/settings.json` allow/deny lists). Draft to the detected convention; if history is inconsistent, follow the most recent consistent pattern and mention the inconsistency once.
