"""Compare two eval runs: what changed between them, and which cases were gained or lost.

    python evals/compare.py                       # the two most recent runs
    python evals/compare.py A.json B.json         # two chosen runs (A = before, B = after)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

RESULTS = Path(__file__).resolve().parent / "results"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    if len(sys.argv) == 3:
        a_path, b_path = Path(sys.argv[1]), Path(sys.argv[2])
    else:
        runs = sorted(RESULTS.glob("*.json"))  # names start with a timestamp; file times are reset by a fresh checkout
        if len(runs) < 2:
            raise SystemExit("Need two runs in evals/results/ (run evals/run.py twice).")
        a_path, b_path = runs[-2], runs[-1]
    a, b = load(a_path), load(b_path)
    sa, sb = a["summary"], b["summary"]

    print(f"A: {a_path.name}  ({sa['label'] or 'no label'})")
    print(f"B: {b_path.name}  ({sb['label'] or 'no label'})")
    changed = [k for k in ("prompt", "model", "structured", "thesis", "cases") if sa.get(k) != sb.get(k)]
    print("Changed between A and B: " + (", ".join(f"{k} {sa.get(k)} -> {sb.get(k)}" for k in changed) or "nothing in the setup"))
    if len(changed) > 1:
        print("  ! More than one thing changed: you cannot tell which one explains the difference.")
    print(f"Accuracy: {sa['accuracy']:.0%} -> {sb['accuracy']:.0%}   parse errors: {sa['parse_errors']} -> {sb['parse_errors']}")

    ra = {c["id"]: c for c in a["cases"]}
    rb = {c["id"]: c for c in b["cases"]}
    gained = [i for i in rb if i in ra and not ra[i]["ok"] and rb[i]["ok"]]
    lost = [i for i in rb if i in ra and ra[i]["ok"] and not rb[i]["ok"]]
    still = [i for i in rb if i in ra and not ra[i]["ok"] and not rb[i]["ok"]]
    new = [i for i in rb if i not in ra]
    for title, ids in (("Gained (KO -> OK)", gained), ("Lost (OK -> KO), a regression", lost), ("Still failing", still), ("New cases", new)):
        print(f"\n{title}: {len(ids)}")
        for i in ids:
            before = f"{ra[i]['got']} -> " if i in ra else ""
            print(f"  {i:<34} expected {rb[i]['expected']:<7} got {before}{rb[i]['got']}")


if __name__ == "__main__":
    main()
