"""PreToolUse guard: block any Write or Edit to the frozen data and to the golden eval cases.

Claude Code passes the tool call as JSON on stdin. Exit 2 = block (the stderr line is sent back to Claude as the reason),
exit 0 = allow. Covers data/ and evals/cases (no trailing slash, so evals/cases_<sector>/ is frozen too).
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

FROZEN = ("data/", "evals/cases")
REASON = ("Blocked: {path} is frozen. data/ is the shared dataset and evals/cases* are the golden tests: "
          "a human edits them by hand in the editor, never the AI.")


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError) as exc:
        print(f"Blocked: the guard could not read the tool call ({exc}).", file=sys.stderr)
        return 2
    file_path = (payload.get("tool_input") or {}).get("file_path") or ""
    if not file_path:
        return 0
    project = Path(os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd") or os.getcwd()).resolve()
    target = Path(file_path)
    if not target.is_absolute():
        target = project / target
    try:
        relative = target.resolve().relative_to(project).as_posix()
    except ValueError:
        return 0  # outside the project: not ours to guard
    # Windows paths are case-insensitive: compare in lower case so Data/ or EVALS/cases is caught too.
    if relative.lower().startswith(FROZEN):
        print(REASON.format(path=relative), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
