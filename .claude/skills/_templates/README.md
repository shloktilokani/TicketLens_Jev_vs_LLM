# Templates

Opt-in templates for projects that use this skills library, plus the skeleton for new skills.
Nothing here is active until copied into a project and wired up. `skillpack install` ships this
folder (except `project/`) into a Claude Code project as `.claude/skills/_templates/`.

They exist because rules written only as prose are followed far less reliably than rules enforced
by a mechanism (see `agent-verification-and-guardrails`). Each template turns one library
convention into something the harness enforces or reminds about.

## Files

| File | Purpose |
|---|---|
| `skill/SKILL.md` | Skeleton for a new skill: frontmatter shape, the nine sections, and the rules `skillpack validate` checks. |
| `claude/hooks/skill_drift.py` | SessionStart hook. Runs `skillpack check` against the master clone and reports drift once per change: new master skills, updatable skills, skills tailored outside their block, project-only skills. |
| `claude/hooks/guard_paths.py` | PreToolUse hook. Hard-denies edits under folders listed in `GUARD_DENY_PATHS`; optionally adds a routing reminder (`GUARD_REMINDER`) before every other edit. Never returns "allow", so normal permission rules still apply. |
| `claude/settings/hooks.example.json` | Wires the two hooks above plus a routing reminder on every prompt. |
| `claude/settings/readonly-git.example.json` | Allows read-only git and denies every mutating git command. For projects where the user does all commits, pushes, and merges. |
| `claude/settings/master-readonly.example.json` | Lets the agent read the master library (or any reference repo) for comparison but never write to it. |
| `claude/settings/secrets-deny.example.json` | Denies env files, secret-manager reads, raw database clients, and credential files; databases are reached only through wrapper scripts (`safe-database-access`). |
| `claude/settings/memory-hooks.example.json` | Loads `.ai/memory.md` at session start and reminds the agent to update docs after each edit (`documentation-maintainer`). |
| `ci/security.yml` | GitHub Actions: actionlint (catches `${{ github.head_ref }}` script injection) and gitleaks over only the new commits, with SHA-pinned actions and checksum-verified tools. |
| `project/README.md` | The README `skillpack` writes into an installed skills folder. Not copied as a template. |

## How to use (Claude Code)

1. Copy the hooks you want from `.claude/skills/_templates/claude/hooks/` to `<project>/.claude/hooks/`.
2. Merge the parts of the `claude/settings/*.example.json` files you want into
   `<project>/.claude/settings.json`. Drop the `$comment` keys.
3. Put per-machine values in `<project>/.claude/settings.local.json` and make sure git ignores it:
   `{"env": {"SKILLS_MASTER_DIR": "/absolute/path/to/Claude_Skills"}}`.
4. The hooks need Python 3 on PATH. Where the interpreter is called `python3`, change the commands.

Other agents: run `python tools/skillpack check --target <project>` for the drift report, and use your
agent's own hook or permission system for the rest.

## Rules & gotchas

- Permission allow-lists match the **whole** command string. Chaining (`a && b`) or adding an unlisted
  flag can make an allowed command stop matching. Run one command per shell call, in the exact shape
  the allow rule names (skills that rely on wrappers say so).
- A hook that returns `"permissionDecision": "allow"` skips the user's permission prompt for that
  call. Guards should only ever deny or add context.
- To stop the agent starting dev servers or other long-running processes, deny their scripts, for
  example `"deny": ["Bash(*start-dev*)"]`; the user starts them.
- Keep project-specific guards (a folder that must never be edited, a project's own wrapper scripts)
  in the project. They don't belong in these templates.
