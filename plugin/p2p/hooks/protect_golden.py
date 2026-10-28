"""PreToolUse guard: data/ and evals/cases* (golden cases) are read-only for Claude. Exit 2 = blocked, 0 = allowed."""
import json
import os
import sys
from pathlib import Path

PROTECTED = ("data", "evals/cases")  # no trailing slash: evals/cases_<sector>/ is covered too


def block(message: str) -> int:
    print(message, file=sys.stderr)
    return 2


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        tool_input = payload["tool_input"]
        file_path = tool_input.get("file_path")
    except (ValueError, KeyError, TypeError, AttributeError):
        return block("Blocked: the guard could not read the tool call, so it refuses the edit (fail closed).")
    if not file_path:
        return 0
    project = Path(os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd") or ".").resolve()
    path = Path(file_path)
    if not path.is_absolute():
        path = project / path  # a relative path is relative to the project, not to this process
    try:
        rel = path.resolve().relative_to(project).as_posix()
    except ValueError:
        return 0  # outside the project
    low = rel.lower()  # Windows and Mac paths are case-insensitive
    for prefix in PROTECTED:
        if low == prefix or low.startswith(prefix + "/") or (prefix == "evals/cases" and low.startswith("evals/cases")):
            return block(f"Blocked: {rel} is frozen. data/ and the golden cases (evals/cases*) are changed by a human, "
                         "by hand, never by Claude.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
