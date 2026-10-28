"""PreToolUse guard: data/ and evals/cases* (golden cases) are read-only for Claude. Exit 2 = blocked, 0 = allowed."""
import json
import os
import sys
from pathlib import Path

PROTECTED = ("data", "evals/cases")  # no trailing slash: evals/cases_<sector>/ is covered too


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        file_path = payload.get("tool_input", {}).get("file_path")
    except (json.JSONDecodeError, AttributeError):
        return 0
    if not file_path:
        return 0
    project = Path(os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd") or ".").resolve()
    try:
        rel = Path(file_path).resolve().relative_to(project).as_posix()
    except ValueError:
        return 0  # outside the project
    for prefix in PROTECTED:
        if rel == prefix or rel.startswith(prefix + "/") or (prefix == "evals/cases" and rel.startswith("evals/cases")):
            print(f"Blocked: {rel} is frozen. data/ and the golden cases (evals/cases*) are changed by a human, by hand, "
                  "never by Claude.", file=sys.stderr)
            return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
