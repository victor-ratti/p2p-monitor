"""Screening filters of the thesis (section 2) applied to data/companies.csv. Deterministic: no language model here.

    python p2p/screen.py [--thesis thesis.md] [--out outputs]

Writes outputs/radar.csv (companies that pass) and outputs/radar_excluded.csv (with the filter that failed).
"""
from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COMPANIES = ROOT / "data" / "companies.csv"


def parse_filters(thesis: Path) -> dict:
    """Read the section 2 table: rows Team, Countries, Market cap, EBITDA margin, Role; columns Min, Max, Your value."""
    text = thesis.read_text(encoding="utf-8")
    section = re.split(r"(?m)^## ", text)
    table = next((s for s in section if s.startswith("2.")), None)
    if table is None:
        raise SystemExit(f"{thesis}: section '## 2.' not found")
    rows = [line for line in table.splitlines() if line.strip().startswith("|")]
    header = [c.strip().lower() for c in rows[0].strip().strip("|").split("|")]
    idx = {name: header.index(name) for name in ("min", "max", "your value") if name in header}
    filters = {}
    for line in rows[2:]:
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        key = cells[0].lower()
        value = cells[idx["your value"]] if "your value" in idx else ""
        low = cells[idx["min"]] if "min" in idx else ""
        high = cells[idx["max"]] if "max" in idx else ""
        filters[key] = {"value": value, "min": _num(low), "max": _num(high)}
    return filters


def _num(text: str):
    text = text.replace(",", "").replace("€", "").replace("%", "").strip()
    try:
        return float(text) if text else None
    except ValueError:
        return None


def _in_list(value: str, allowed: str) -> bool:
    if not allowed:
        return True
    return value.strip().lower() in {a.strip().lower() for a in allowed.split(",") if a.strip()}


def _in_range(value: str, low, high) -> bool:
    if low is None and high is None:
        return True
    if value in ("", None):
        return False
    number = float(value)
    return (low is None or number >= low) and (high is None or number <= high)


def failed_filter(row: dict, filters: dict) -> str:
    """Name of the first filter the company fails, or '' when it passes."""
    checks = [
        ("team", lambda r, f: _in_list(r["team"], f["value"])),
        ("countries", lambda r, f: _in_list(r["country"], f["value"])),
        ("market cap (€m)", lambda r, f: _in_range(r["market_cap_eur_m"], f["min"], f["max"])),
        ("ebitda margin", lambda r, f: _in_range(r["ebitda_margin_ltm"], f["min"], f["max"])),
        ("role", lambda r, f: _in_list(r["role"], f["value"])),
    ]
    for name, check in checks:
        spec = filters.get(name)
        if spec and not check(row, spec):
            return name
    return ""


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--thesis", type=Path, default=ROOT / "thesis.md")
    ap.add_argument("--out", type=Path, default=ROOT / "outputs")
    args = ap.parse_args()
    if not args.thesis.exists():
        raise SystemExit(f"Thesis not found: {args.thesis}. Fill in section 2 of thesis.md, or pass --thesis.")
    filters = parse_filters(args.thesis)
    with open(COMPANIES, encoding="utf-8", newline="") as fh:
        companies = list(csv.DictReader(fh))
    passed, excluded = [], []
    for row in companies:
        failed = failed_filter(row, filters)
        (excluded if failed else passed).append({**row, "failed_filter": failed} if failed else row)
    args.out.mkdir(parents=True, exist_ok=True)
    _write(args.out / "radar.csv", passed, list(companies[0].keys()))
    _write(args.out / "radar_excluded.csv", excluded, list(companies[0].keys()) + ["failed_filter"])
    active = {k: v for k, v in filters.items() if v["value"] or v["min"] is not None or v["max"] is not None}
    print(f"Filters: " + (", ".join(f"{k} = {v['value'] or ''}{'' if v['min'] is None else ' min ' + str(v['min'])}"
                                   f"{'' if v['max'] is None else ' max ' + str(v['max'])}" for k, v in active.items()) or "none"))
    print(f"{len(passed)} of {len(companies)} companies pass -> {args.out / 'radar.csv'}")
    for row in passed:
        print(f"  {row['ticker']:<10} {row['name']:<30} {row['team']:<32} cap EUR {row['market_cap_eur_m']}m, "
              f"margin {row['ebitda_margin_ltm']}, net debt/EBITDA {row['net_debt_to_ebitda'] or 'unknown'}")
    if excluded:
        counts = {}
        for row in excluded:
            counts[row["failed_filter"]] = counts.get(row["failed_filter"], 0) + 1
        print("Excluded: " + ", ".join(f"{n} on {k}" for k, n in counts.items()))


def _write(path: Path, rows: list, fields: list) -> None:
    with open(path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
