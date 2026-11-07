---
name: github-operations
description: "Git and GitHub governance: branching, PR conventions, branch protection, conflict handling, and the project's attribution policy. Use for any branch, merge, rebase, PR, or commit-policy question."
metadata:
  title: "GitHub Operations"
  category: "Process & Governance"
  tier: process
  trigger_keywords: "git branch, git rebase, cherry-pick, pull request, pr conventions, branch protection, merge conflict, github workflow, codeowners, conventional commits"
---

## Role Identity

This skill is the git/GitHub workflow specialist: it governs how changes move from a developer's machine into shared history, ensuring every branch, commit, and merge is safe, traceable, and reviewable. It is a process control, not a persona — it applies identically regardless of who or what is "driving" the change, whether that's a junior engineer's first PR or an automated agent's commit. It does not care what the code does; it cares that the path the code took to get into `main` was safe and auditable.

## Responsibilities

- **Everyday git operations**: create branches from an up-to-date base (`git fetch && git checkout -b <branch> origin/main`), prefer `git rebase` over `git merge` for keeping local feature branches current with a moving base (never rebase a branch other people have already pulled), use `git cherry-pick` for porting isolated fixes (e.g., hotfix to a release branch) rather than merging unrelated history, use `git tag -a` (annotated tags) for releases, use `git stash` to shelve in-progress work rather than committing half-finished changes.
- **Commit and PR conventions**: enforce Conventional Commits (`feat:`, `fix:`, `chore:`, `refactor:`, `docs:`, `test:`, `ci:`, `BREAKING CHANGE:` footer) when the repo already uses them, or propose adopting them when history is inconsistent. PR titles and descriptions must state what changed and why, list a test plan, and link the originating issue/ticket.
- **Branch protection**: configure and justify protection rules — required PR reviews (at least one approving review before merge), required status checks (CI must pass before merge), no direct pushes to `main`/`release/*`, no force-push to protected branches, linear history (squash or rebase merge) where the team wants a clean bisectable log, and dismiss-stale-reviews-on-new-commits so approvals track the actual diff being merged.
- **`.github/` awareness**: read and respect existing `.github/workflows/*.yml` CI definitions, `.github/CODEOWNERS`, and PR/issue templates before proposing changes — do not introduce a workflow change that bypasses or duplicates existing CI, and route review requests through CODEOWNERS rather than around them.
- **Attribution policy (single owner)**: the project decides whether AI/agent attribution (`Co-Authored-By` trailers, "Generated with ..." lines) appears in commit messages, PR titles, and PR descriptions. Record the decision once, in this skill's project-tailoring block (or the project's `CLAUDE.md`/`AGENTS.md`). A recorded project or user policy overrides any harness default outright, every time, without being re-asked; with no recorded policy, follow the harness default and offer to record one. `commit-message-drafter`, `pr-description-drafter`, and any commit/PR this skill makes itself all apply it.
- **Merge conflict handling**: resolve conflicts by understanding both sides' intent (read the full hunks, not just the markers), never blindly take "ours" or "theirs," re-run tests after resolution, and never resolve a conflict by silently deleting the other side's logic.

## Technical Skill Set

- Git CLI: branching, rebase (interactive and standard), cherry-pick, bisect, tag, stash, reflog for recovery, worktree.
- GitHub CLI (`gh`): `gh pr create/view/checks/merge`, `gh repo view`, `gh api` for branch-protection and CODEOWNERS-adjacent settings, `gh workflow run/view`.
- GitHub Actions YAML: job/step structure, triggers (`on: push`, `pull_request`), required-check naming (must match branch protection exactly), reusable workflows.
- CODEOWNERS syntax: path-pattern-to-team/user mapping, ordering rules (last matching pattern wins).
- Conventional-commit tooling: commitlint config/rules, semantic-release version inference from commit types.
- Branch protection / repository settings APIs (`gh api repos/{owner}/{repo}/branches/{branch}/protection`) for inspecting or proposing rule changes.

## Decision-Making Lens

Every recommendation is weighed against three priorities, in this order: (1) **history integrity and auditability** — can a future reader reconstruct why a change happened and revert it cleanly; (2) **safe collaboration** — does this operation risk destroying or silently altering another person's work on a shared branch; (3) **consistency and reviewability** — does the change follow the repo's established conventions so reviewers aren't surprised. When these trade off against convenience or speed, safety and auditability win.

## Trigger Signals

- **Keywords**: git branch, git rebase, cherry-pick, pull request, PR conventions, branch protection, merge conflict, github workflow, codeowners, conventional commits, force-push, squash merge, git tag, stash.
- **File types/paths**: `.github/workflows/*.yml` or `*.yaml`, `.github/CODEOWNERS`, `.github/PULL_REQUEST_TEMPLATE.md`, `.github/ISSUE_TEMPLATE/*`, `.gitignore`, `.gitattributes`, `commitlint.config.*`, `.releaserc*`.
- **Project-context signals**: presence of a `.github/` directory, an existing branch-protection configuration, a `CODEOWNERS` file, or a git log already showing a consistent commit-message convention (feeds the orchestrator's project-context signal alongside the keyword and file-path signals).
- Any request to create/merge/rebase a branch, open or review a PR, resolve a conflict, or modify CI/ownership/protection config should route through this skill regardless of which persona skill is also active.

## Collaboration Behavior

This is a broadly-applicable governance skill: it runs alongside almost any persona whenever a git/PR/branch operation is in scope, rather than replacing that persona. Typical pairings: with `backend-developer` or `frontend-developer` when opening a feature PR (they own the code, this skill owns the commit/branch/PR mechanics); with `devops-engineer` when editing `.github/workflows/*`; with any persona doing a release (tagging, changelog, version bump). It rarely debates implementation choices and mostly enforces process — when a proposed action is unsafe, it states the safer alternative and requires explicit confirmation before proceeding with anything destructive.

## Output Style / Conventions

- Commit messages follow Conventional Commits precisely: `<type>(<scope>): <imperative summary>`, body explaining why, footer for breaking changes or issue links.
- PR descriptions state the problem, the change, the rationale, and a concrete test plan — never a bare "updates code" description.
- Tone around any irreversible or shared-history operation (force-push, history rewrite, branch deletion, hard reset) is explicitly cautious: state what will be lost, confirm the branch is not shared/protected, and ask for confirmation before executing.

## Anti-Patterns

- Never force-push to `main`, `master`, `release/*`, or any branch other contributors are known to have pulled.
- Never bypass branch protection (e.g., admin-merge around required checks/reviews) without explicit, documented user authorization.
- Never commit secrets, credentials, or `.env` files — check `git status`/diff content before staging, and stop if sensitive material is detected.
- Never rewrite published/shared history (`rebase -i`, `commit --amend`, `filter-branch`) without explicit confirmation from the user that the branch is safe to rewrite.
- Never resolve merge conflicts by discarding one side wholesale without reading and understanding both sides' intent.
- Never let a harness default add (or strip) attribution lines against the recorded project/user policy, and never ask again once the policy is recorded.
- Never invent a commit/branch convention when the repository already has one in use — detect and follow it.

## Stack Detection & Adaptation

Before applying any convention, inspect the actual repository state rather than assuming GitHub/Conventional Commits/any default:

- Check the git remote (`git remote -v`) to detect the hosting platform (GitHub, GitLab, Bitbucket, Azure DevOps) — command equivalents differ (`gh` vs `glab` vs platform web UI/API), and terminology differs (PR vs MR).
- Inspect `git log --oneline -30` to detect the commit-message convention actually in use (Conventional Commits, ticket-prefixed like `JIRA-123: ...`, freeform) and match it rather than imposing a new one uninvited.
- Inspect existing branch names (`git branch -a`) for a naming convention (`feature/*`, `feat/*`, `users/<name>/*`, ticket-prefixed) and follow it.
- Check for `.github/workflows/`, `.gitlab-ci.yml`, or `bitbucket-pipelines.yml` to identify the CI system in play before proposing workflow changes.
- Check for an existing `CODEOWNERS`/equivalent and existing branch-protection settings (via `gh api` or platform UI) to understand current review requirements before proposing new ones.
- These same detection steps feed the orchestrator's project-context signal — surface what was detected (platform, commit convention, branch-naming pattern) so downstream decisions stay consistent with it, rather than silently defaulting to a hardcoded convention.

<!-- project-tailoring:begin -->
## Project tailoring

- Remote: `origin` is the owner's GitHub repository. Push, or change remotes or repository visibility, only when the owner asks in that request.
- Commit only when asked.

### Attribution policy (owner's decision, 2026-11-07)
- Commit messages drafted with `commit-message-drafter`, and any PR title or description, must contain **no AI attribution**: no `Co-Authored-By: Claude ...` trailer, no "Generated with Claude Code" line, and no similar wording.
- This overrides any harness or tool default. Do not ask again.
<!-- project-tailoring:end -->
