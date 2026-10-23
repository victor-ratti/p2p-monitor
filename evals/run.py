"""Replay every eval case through the judge and score it. This is the test suite of the judge.

    python evals/run.py                                   # prompt v1, model haiku, all cases
    python evals/run.py --prompt v2 --model sonnet --label "rules added"
    python evals/run.py --only 003,005 --workers 2        # a few cases, less parallelism
    python evals/run.py --structured                      # extension: force the JSON shape with a schema

Writes evals/results/<timestamp>-<model>-<prompt>.json. Compare two runs with `python evals/compare.py`.
Rule of the game: change ONE thing between two runs (the prompt, OR the model, OR a case), never two.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from p2p.judge import EVAL_THESIS, VERDICTS, judge, load_case, load_thesis  # noqa: E402

CASES = ROOT / "evals" / "cases"
RESULTS = ROOT / "evals" / "results"


def run_case(path: Path, thesis: str, prompt: str, model: str, structured: bool) -> dict:
    case = load_case(path)
    out = judge(case["input"], thesis, prompt, model, structured)
    return {"id": case["id"], "title": case.get("title", ""), "expected": case["expected"], "got": out["verdict"],
            "ok": out["verdict"] == case["expected"], "backend": out["backend"], "reasons": out["reasons"], "missing_facts": out["missing_facts"],
            "parse_error": out.get("parse_error"), "duration_s": out["duration_s"], "cost_usd": out["cost_usd"],
            "tags": case.get("tags", []), "raw": out["raw"]}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--prompt", default="v1")
    ap.add_argument("--model", default="haiku")
    ap.add_argument("--thesis", type=Path, default=EVAL_THESIS)
    ap.add_argument("--cases", type=Path, default=CASES)
    ap.add_argument("--only", help="comma-separated case id prefixes, e.g. 003,005")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--structured", action="store_true")
    ap.add_argument("--label", default="", help="a few words on what changed since the last run")
    ap.add_argument("--fail-under", type=float, help="exit 1 when accuracy is below this fraction (for CI)")
    args = ap.parse_args()

    paths = sorted(args.cases.glob("*.json"))
    if args.only:
        wanted = [w.strip() for w in args.only.split(",")]
        paths = [p for p in paths if any(p.name.startswith(w) for w in wanted)]
    if not paths:
        raise SystemExit(f"No case found in {args.cases}")
    thesis = load_thesis(args.thesis)

    print(f"Judging {len(paths)} cases with prompt {args.prompt}, model {args.model}, {args.workers} in parallel...")
    started = time.time()
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        rows = list(pool.map(lambda p: run_case(p, thesis, args.prompt, args.model, args.structured), paths))
    wall = round(time.time() - started, 1)

    correct = sum(r["ok"] for r in rows)
    confusion = {e: {g: 0 for g in list(VERDICTS) + ["ParseError", "Error"]} for e in VERDICTS}
    for r in rows:
        confusion.setdefault(r["expected"], {})[r["got"]] = confusion.get(r["expected"], {}).get(r["got"], 0) + 1
    costs = [r["cost_usd"] for r in rows if r["cost_usd"] is not None]
    summary = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "label": args.label, "prompt": args.prompt,
        "model": args.model, "structured": args.structured, "thesis": str(args.thesis.relative_to(ROOT)) if args.thesis.is_relative_to(ROOT) else str(args.thesis),
        "backend": rows[0].get("backend", ""), "cases": len(rows), "correct": correct, "accuracy": round(correct / len(rows), 3),
        "parse_errors": sum(r["got"] == "ParseError" for r in rows), "errors": sum(r["got"] == "Error" for r in rows),
        "confusion": confusion, "total_cost_usd": round(sum(costs), 4) if costs else None, "wall_s": wall,
    }
    RESULTS.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out = RESULTS / f"{stamp}-{args.model}-{args.prompt}{'-structured' if args.structured else ''}.json"
    out.write_text(json.dumps({"summary": summary, "cases": rows}, ensure_ascii=False, indent=2), encoding="utf-8")

    print()
    print(f"{'case':<34} {'expected':<9} {'got':<11} ok   note")
    for r in rows:
        note = r["parse_error"] or (r["reasons"][0][:70] if r["reasons"] else "")
        print(f"{r['id']:<34} {r['expected']:<9} {r['got']:<11} {'OK ' if r['ok'] else 'KO '}  {note}")
    print()
    print(f"Accuracy: {correct}/{len(rows)} = {summary['accuracy']:.0%}   parse errors: {summary['parse_errors']}   "
          f"errors: {summary['errors']}   wall time: {wall}s" + (f"   cost: ${summary['total_cost_usd']}" if costs else ""))
    print("Confusion (rows = expected, columns = got):")
    cols = list(VERDICTS) + ["ParseError", "Error"]
    print(f"{'':<10}" + "".join(f"{c:>11}" for c in cols))
    for e in VERDICTS:
        print(f"{e:<10}" + "".join(f"{confusion[e].get(c, 0):>11}" for c in cols))
    print(f"\nSaved: {out.relative_to(ROOT)}   (compare two runs: python evals/compare.py)")
    if args.fail_under is not None and summary["accuracy"] < args.fail_under:
        sys.exit(1)


if __name__ == "__main__":
    main()
