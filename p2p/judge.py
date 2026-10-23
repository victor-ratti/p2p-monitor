"""Judge ONE company against the investment thesis: Priority, Radar or Reject.

    python p2p/judge.py --ticker SBS.DE                          # a company of data/companies.csv, thesis ./thesis.md
    python p2p/judge.py --case evals/cases/003-leverage-just-above.json   # an eval case, thesis evals/thesis_diagnostics.md
    python p2p/judge.py --radar                                  # every company of outputs/radar.csv -> outputs/judgments.csv
    options: --thesis PATH   --prompt v1|v2|...   --model haiku|sonnet   --structured   --json   --workers 4

Verdicts: Priority (we would buy at the right price), Radar (fits the strategy, keep watching), Reject (a kill criterion).
Actionable is NOT a verdict: p2p/dashboard.py grants it to a Priority company whose takeout price is below the target price.

The only place where a language model judges. The code computes nothing here: the figures (leverage, margins, price
moves) come from data/companies.csv, already computed. The prompt is `prompts/judge_<version>.md`.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from p2p.llm import complete  # noqa: E402

VERDICTS = ("Priority", "Radar", "Reject")
COMPANIES = ROOT / "data" / "companies.csv"
FACTS = ROOT / "data" / "facts"
PROMPTS = ROOT / "prompts"
DEFAULT_THESIS = ROOT / "thesis.md"
EVAL_THESIS = ROOT / "evals" / "thesis_diagnostics.md"

# Extension (Part 2): pass this to complete(schema=...) with --structured. The model is then forced to answer in this
# exact shape (Claude Code `--json-schema`), which removes parsing errors for good.
SCHEMA = {
    "type": "object",
    "properties": {
        "verdict": {"type": "string", "enum": list(VERDICTS)},
        "reasons": {"type": "array", "items": {"type": "string"}},
        "missing_facts": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["verdict", "reasons", "missing_facts"],
    "additionalProperties": False,
}


def load_prompt(version: str) -> str:
    path = PROMPTS / f"judge_{version}.md"
    if not path.exists():
        raise SystemExit(f"Prompt not found: {path} (available: {', '.join(p.stem for p in PROMPTS.glob('judge_*.md'))})")
    return path.read_text(encoding="utf-8")


def load_thesis(path: Path) -> str:
    """Sections 1 and 3 of the thesis (strategy, judgment criteria): the only parts the judge needs."""
    text = path.read_text(encoding="utf-8")
    parts = re.split(r"(?m)^## ", text)
    keep = [p for p in parts if p.startswith("1.") or p.startswith("3.")]
    if not keep:
        raise SystemExit(f"{path}: sections '## 1.' and '## 3.' not found")
    return "\n\n".join("## " + p.strip() for p in keep)


def load_company(ticker: str) -> dict:
    with open(COMPANIES, encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            if row["ticker"] == ticker:
                facts = FACTS / f"{ticker}.md"
                return {"company": row, "facts": facts.read_text(encoding="utf-8") if facts.exists() else "No facts file."}
    raise SystemExit(f"{ticker} is not in {COMPANIES.relative_to(ROOT)}")


def load_case(path: Path) -> dict:
    case = json.loads(path.read_text(encoding="utf-8"))
    inp = case["input"]
    if "company" not in inp and "ticker" in inp:  # a real company of the dataset
        inp = load_company(inp["ticker"])
    case["input"] = inp
    return case


def render_input(inp: dict) -> str:
    company = inp["company"]
    lines = ["# Company profile"]
    lines += [f"- {key}: {value if value not in (None, '') else 'unknown'}" for key, value in company.items()]
    lines += ["", "# Facts", (inp.get("facts") or "").strip() or "No further facts."]
    return "\n".join(lines)


def parse_verdict(text: str) -> dict:
    """Find a JSON object in the answer. Anything else is a ParseError, which the eval counts as a failure."""
    match = re.search(r"\{.*\}", text, re.S)
    if not match:
        return _unparsed("no JSON object in the answer")
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError as exc:
        return _unparsed(f"invalid JSON: {exc}")
    verdict = str(data.get("verdict", "")).strip().capitalize()
    if verdict not in VERDICTS:
        return _unparsed(f"verdict '{data.get('verdict')}' is not Priority, Radar or Reject")
    reasons = data.get("reasons") or []
    missing = data.get("missing_facts") or []
    return {"verdict": verdict,
            "reasons": [str(r) for r in ([reasons] if isinstance(reasons, str) else reasons)],
            "missing_facts": [str(m) for m in ([missing] if isinstance(missing, str) else missing)]}


def _unparsed(why: str) -> dict:
    return {"verdict": "ParseError", "reasons": [], "missing_facts": [], "parse_error": why}


def judge(inp: dict, thesis: str, prompt_version: str = "v1", model: str = "haiku", structured: bool = False) -> dict:
    system = load_prompt(prompt_version)
    user = f"# Investment thesis\n\n{thesis}\n\n{render_input(inp)}"
    result = complete(system, user, model=model, schema=SCHEMA if structured else None)
    if result.error:
        out = {"verdict": "Error", "reasons": [], "missing_facts": [], "parse_error": result.error}
    elif result.structured:
        out = parse_verdict(json.dumps(result.structured))
    else:
        out = parse_verdict(result.text)
    out.update({"model": result.model, "backend": result.backend, "prompt": prompt_version,
                "duration_s": result.duration_s, "cost_usd": result.cost_usd, "raw": result.text})
    return out


JUDGMENTS = ROOT / "outputs" / "judgments.csv"
JUDGMENT_COLUMNS = ["ticker", "verdict", "final_verdict", "judged_on", "prompt", "model", "note"]


def judge_radar(thesis_path: Path, prompt_version: str, model: str, structured: bool, workers: int) -> None:
    """Judge every ticker of outputs/radar.csv and write outputs/judgments.csv (final_verdict = the model's, until a
    person overrides it: the judge skill does that). Rows of tickers no longer on the radar are kept."""
    from concurrent.futures import ThreadPoolExecutor
    from datetime import date
    radar = ROOT / "outputs" / "radar.csv"
    if not radar.exists():
        raise SystemExit("outputs/radar.csv not found: run python p2p/screen.py first")
    if not thesis_path.exists():
        raise SystemExit(f"Thesis not found: {thesis_path}. Fill in thesis.md first (or pass --thesis).")
    with open(radar, encoding="utf-8", newline="") as fh:
        tickers = [row["ticker"] for row in csv.DictReader(fh)]
    thesis = load_thesis(thesis_path)
    print(f"Judging {len(tickers)} radar companies with prompt {prompt_version}, model {model}...")
    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(lambda t: (t, judge(load_company(t), thesis, prompt_version, model, structured)), tickers))
    existing = {}
    if JUDGMENTS.exists():
        with open(JUDGMENTS, encoding="utf-8", newline="") as fh:
            existing = {row["ticker"]: row for row in csv.DictReader(fh)}
    today = date.today().isoformat()
    for ticker, out in results:
        note = out.get("parse_error") or (out["reasons"][0] if out["reasons"] else "")
        existing[ticker] = {"ticker": ticker, "verdict": out["verdict"], "final_verdict": out["verdict"], "judged_on": today,
                            "prompt": prompt_version, "model": out["model"], "note": note[:300]}
        print(f"  {ticker:<10} {out['verdict']:<11} {note[:90]}")
    JUDGMENTS.parent.mkdir(exist_ok=True)
    with open(JUDGMENTS, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=JUDGMENT_COLUMNS)
        writer.writeheader()
        writer.writerows(existing[t] for t in sorted(existing))
    counts = {}
    for _, out in results:
        counts[out["verdict"]] = counts.get(out["verdict"], 0) + 1
    print(f"Wrote {JUDGMENTS.relative_to(ROOT)}: " + ", ".join(f"{n} {v}" for v, n in counts.items())
          + ". Next: python p2p/dashboard.py")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    who = ap.add_mutually_exclusive_group(required=True)
    who.add_argument("--ticker", help="a ticker of data/companies.csv")
    who.add_argument("--case", type=Path, help="an eval case file (evals/cases/*.json)")
    who.add_argument("--radar", action="store_true", help="judge every company of outputs/radar.csv, write outputs/judgments.csv")
    ap.add_argument("--workers", type=int, default=4, help="parallel model calls with --radar")
    ap.add_argument("--thesis", type=Path, help="thesis file (default: ./thesis.md, or evals/thesis_diagnostics.md for a case)")
    ap.add_argument("--prompt", default="v1", help="prompt version: prompts/judge_<version>.md")
    ap.add_argument("--model", default="haiku")
    ap.add_argument("--structured", action="store_true", help="force the JSON shape with a schema (extension)")
    ap.add_argument("--json", action="store_true", help="print the full result as JSON")
    args = ap.parse_args()

    if args.radar:
        judge_radar(args.thesis or DEFAULT_THESIS, args.prompt, args.model, args.structured, args.workers)
        return
    if args.case:
        case = load_case(args.case)
        inp, label, thesis_path = case["input"], case["id"], args.thesis or EVAL_THESIS
        expected = case.get("expected")
    else:
        inp, label, thesis_path, expected = load_company(args.ticker), args.ticker, args.thesis or DEFAULT_THESIS, None
    if not thesis_path.exists():
        raise SystemExit(f"Thesis not found: {thesis_path}. Fill in thesis.md first (or pass --thesis).")

    out = judge(inp, load_thesis(thesis_path), args.prompt, args.model, args.structured)
    out["id"] = label
    if expected is not None:
        out["expected"] = expected
    if args.json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return
    tail = f" (expected {expected})" if expected else ""
    print(f"{label} -> {out['verdict']}{tail}   [{out['model']}, prompt {out['prompt']}, {out['duration_s']}s]")
    for reason in out["reasons"]:
        print(f"  - {reason}")
    if out["missing_facts"]:
        print("  missing facts: " + "; ".join(out["missing_facts"]))
    if out.get("parse_error"):
        print(f"  ! {out['parse_error']}")
        if out["raw"]:
            print("  raw answer: " + out["raw"][:400].replace("\n", " "))


if __name__ == "__main__":
    main()
