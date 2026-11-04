#!/usr/bin/env python3
"""PreToolUse hook for Edit|Write|NotebookEdit: hard-deny edits under protected folders, and
optionally remind the agent of the routing rules on every other edit.

Configure with environment variables (in .claude/settings.json "env"):
    GUARD_DENY_PATHS   comma-separated folders, relative to the project root, that must never be
                       edited (e.g. "legacy/,vendor/,.claude/skills/_templates/")
    GUARD_DENY_REASON  message shown when an edit is denied (optional)
    GUARD_REMINDER     text added to the agent's context before every other edit (optional)

It never returns "allow": paths it does not deny go through Claude Code's normal permission
rules unchanged. Denials match whole folders, so "legacy_notes.md" is not caught by "legacy/".
"""
import json
import os
import posixpath
import re
import sys


def norm(path: str) -> str:
    """Absolute-ish, case-folded, '..'-collapsed, forward-slash form; 'C:/x' and '/c/x' compare equal."""
    p = path.replace("\\", "/")
    m = re.match(r"^([A-Za-z]):/(.*)$", p)
    if m:
        p = "/" + m.group(1) + "/" + m.group(2)
    return posixpath.normpath("/" + p.lstrip("/")).lower().rstrip("/") + "/"


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        payload = {}
    tool_input = payload.get("tool_input") or {}
    raw = str(tool_input.get("file_path") or tool_input.get("notebook_path") or "")
    project = norm(os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd") or os.getcwd())
    target = norm(raw)
    if target.startswith(project) and target != project:
        target = "/" + target[len(project):]
    denied = [d for d in (x.strip() for x in os.environ.get("GUARD_DENY_PATHS", "").split(",")) if d]
    out: dict = {"hookEventName": "PreToolUse"}
    if any(target.startswith(norm(d)) for d in denied):
        out["permissionDecision"] = "deny"
        out["permissionDecisionReason"] = os.environ.get(
            "GUARD_DENY_REASON", "This folder is read-only for the agent. Reading and searching it are fine; "
            "do not edit it and do not ask for permission to. The owner will say when a change is wanted.")
    elif os.environ.get("GUARD_REMINDER"):
        out["additionalContext"] = os.environ["GUARD_REMINDER"]
    else:
        return 0
    print(json.dumps({"hookSpecificOutput": out}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
