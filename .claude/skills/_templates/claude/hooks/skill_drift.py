#!/usr/bin/env python3
"""SessionStart hook: report drift between this project's skills and the master library.

Runs ``skillpack check --json`` from the master clone and, when something needs attention, tells
the agent (additionalContext) and the user (systemMessage). It reports a given situation once:
the next report happens only when the drift changes.

Configure in .claude/settings.local.json (per machine, not committed):
    "env": {"SKILLS_MASTER_DIR": "/absolute/path/to/Claude_Skills"}
The hook exits silently when SKILLS_MASTER_DIR is unset or the clone is missing, so the shared
.claude/settings.json can wire it up for everyone.
"""
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

ACTIONABLE = {
    "new in master": "new in the master (adopt or decline with `skillpack install --exclude`)",
    "update available": "updatable from the master (`skillpack update --target .`)",
    "tailored + master changed": "edited outside the tailoring block while the master changed (merge by hand)",
    "unmanaged (run adopt)": "not yet managed by skillpack (`skillpack adopt --target .`)",
    "project-only": "project-only (generalise into the master, or `skillpack acknowledge`)",
    "removed from master": "removed from the master",
}


def find_master(value: str) -> Path | None:
    root = Path(value).expanduser()
    for cand in (root, root.parent, root.parent.parent):  # also accept .../skills or .../.claude/skills
        if (cand / "tools" / "skillpack" / "__main__.py").exists():
            return cand
    return None


def main() -> int:
    master = find_master(os.environ.get("SKILLS_MASTER_DIR", ""))
    if master is None:
        return 0
    project = Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
    try:
        proc = subprocess.run([sys.executable, str(master / "tools" / "skillpack"), "check", "--target",
                               str(project), "--json"], capture_output=True, text=True, timeout=60)
        report = json.loads(proc.stdout)
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError):
        return 0
    found: list[str] = []
    for root in report.get("roots", []):
        if not root.get("manifest"):
            found.append(f"{root['dir']}/ has no skillpack manifest (`skillpack adopt --target .`)")
        for key, label in ACTIONABLE.items():
            names = root.get("status", {}).get(key)
            if names:
                found.append(f"{root['dir']}/ {label}: {', '.join(names)}")
    if not found:
        return 0
    signature = hashlib.sha256("\n".join(found).encode()).hexdigest()
    state = project / ".claude" / ".skillpack-drift-seen"
    try:
        if state.read_text(encoding="utf-8").strip() == signature:
            return 0
    except OSError:
        pass
    try:
        state.parent.mkdir(parents=True, exist_ok=True)
        state.write_text(signature, encoding="utf-8")
    except OSError:
        pass
    context = ("Skill-library drift between this project and the master library "
               f"({report.get('master_commit', '?')}): " + "; ".join(found) +
               ". Mention this to the user once; do not act on it unless asked.")
    print(json.dumps({"systemMessage": f"Skill drift: {len(found)} item(s); see `skillpack check --target .`",
                      "hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": context}}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
