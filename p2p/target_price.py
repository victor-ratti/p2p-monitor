"""Target price per share: the most the fund can pay (ability to pay, a 5-year LBO) and the multiple price.
Deterministic: code, never the model. Method and worked example: docs/target-price.md.

    python p2p/target_price.py --ticker SBS.DE [--thesis thesis.md] [--exit-margin 0.18] [--json]

Settings come from thesis.md section 4 (blank = default). Figures come from data/market.json (frozen dataset).
"""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, replace
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parent.parent
MARKET = ROOT / "data" / "market.json"


@dataclass(frozen=True)
class Settings:
    method: str = "lbo"                 # lbo | multiple | lower
    reference_multiple: float = 13.0
    target_irr: float = 0.25
    holding_years: int = 5
    leverage: float = 4.0
    exit_multiple: float = 12.0
    revenue_growth: float = 0.05
    exit_margin: Optional[float] = None  # None = keep today's margin
    cash_conversion: float = 0.50
    interest_rate: float = 0.075
    fees: float = 0.03
    control_premium: float = 0.30
    near_threshold: float = 0.05


SETTING_KEYS = {
    "Target price method": ("method", str), "Reference multiple": ("reference_multiple", float),
    "Target IRR": ("target_irr", float), "Holding period": ("holding_years", int), "Leverage": ("leverage", float),
    "Exit multiple": ("exit_multiple", float), "Revenue growth": ("revenue_growth", float),
    "Exit EBITDA margin": ("exit_margin", float), "Cash conversion": ("cash_conversion", float),
    "Interest rate": ("interest_rate", float), "Fees": ("fees", float), "Control premium": ("control_premium", float),
    "Near threshold": ("near_threshold", float),
}


def as_number(text) -> Optional[float]:
    """'13x' -> 13, '25%' -> 0.25, '4.0x' -> 4.0, '' -> None."""
    if text is None:
        return None
    s = str(text).replace("`", "").replace(",", "").strip()
    m = re.match(r"^[-+]?\d+(?:\.\d+)?", s)
    if not m:
        return None
    value = float(m.group(0))
    return value / 100 if s[m.end():].lstrip().startswith("%") else value


def round_price(x: Optional[float]) -> Optional[float]:
    """Display rounding, half-up to the cent (4 decimals below 1)."""
    if x is None:
        return None
    d = Decimal(str(round(float(x), 9)))
    step = Decimal("0.0001") if abs(d) < 1 else Decimal("0.01")
    return float(d.quantize(step, rounding=ROUND_HALF_UP))


def read_settings(thesis: Path) -> Settings:
    """Section 4 of the thesis: rows '| Setting | ... | Default | Your value |'. Blank or 'default' keeps the default."""
    if not thesis.exists():
        return Settings()
    parts = re.split(r"(?m)^## ", thesis.read_text(encoding="utf-8"))
    section = next((p for p in parts if p.startswith("4.")), "")
    rows = [l for l in section.splitlines() if l.strip().startswith("|")]
    if len(rows) < 2:
        return Settings()
    header = [c.strip().lower() for c in rows[0].strip().strip("|").split("|")]
    col = header.index("your value") if "your value" in header else -1
    overrides = {}
    for line in rows[2:]:
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if cells[0] not in SETTING_KEYS or col < 0 or col >= len(cells):
            continue
        raw = cells[col].replace("`", "").strip()
        if not raw or raw.lower() == "default":
            continue
        attr, kind = SETTING_KEYS[cells[0]]
        if kind is str:
            overrides[attr] = raw.lower().split(" (")[0].strip()
        else:
            n = as_number(raw)
            if n is not None:
                overrides[attr] = int(n) if kind is int else n
    return replace(Settings(), **overrides)


def load_market() -> dict:
    return json.loads(MARKET.read_text(encoding="utf-8"))["companies"]


def ability_to_pay(revenue: float, ebitda: float, net_debt: float, shares: float, s: Settings) -> Optional[dict]:
    """5-year LBO worked backwards from the exit. None when EBITDA is not positive (NM)."""
    if not ebitda or ebitda <= 0 or not revenue or not shares:
        return None
    n = s.holding_years
    debt0 = s.leverage * ebitda
    m0 = ebitda / revenue
    m_exit = m0 if s.exit_margin is None else s.exit_margin
    rows, debt = [(0, revenue, ebitda, None, debt0)], debt0
    for t in range(1, n + 1):
        rev = revenue * (1 + s.revenue_growth) ** t
        e = rev * (m0 + (m_exit - m0) * t / n)                        # margin moves in a straight line
        free_cash = s.cash_conversion * e - s.interest_rate * debt    # interest on opening debt
        debt -= free_cash                                             # free cash repays debt
        rows.append((t, rev, e, free_cash, debt))
    exit_value = s.exit_multiple * rows[-1][2]
    equity_exit = exit_value - debt
    cheque = equity_exit / (1 + s.target_irr) ** n
    max_ev = (cheque + debt0) / (1 + s.fees)
    max_price = (max_ev - net_debt) / shares

    def irr_at(price: float) -> Optional[float]:
        paid = (price * shares + net_debt) * (1 + s.fees) - debt0
        return (equity_exit / paid) ** (1 / n) - 1 if paid > 0 and equity_exit > 0 else None

    return {"max_price": max_price, "irr_at": irr_at, "debt0": debt0, "rows": rows, "exit_value": exit_value,
            "equity_exit": equity_exit, "cheque": cheque, "max_ev": max_ev, "exit_margin_used": m_exit}


def evaluate(ticker: str, market: dict, s: Settings) -> dict:
    """All valuation figures for one company, unrounded. Missing inputs stay None; non-positive EBITDA gives 'NM'."""
    m = market.get(ticker)
    if m is None:
        raise SystemExit(f"{ticker} is not in {MARKET.relative_to(ROOT)}")
    revenue, ebitda, shares, price = m.get("revenue_ttm"), m.get("ebitda_ttm"), m.get("shares_outstanding"), m.get("price")
    debt, cash = m.get("total_debt"), m.get("total_cash")
    net_debt = None if debt is None or cash is None else debt - cash
    out = {"ticker": ticker, "price": price, "currency": m.get("currency"), "revenue": revenue, "ebitda": ebitda,
           "net_debt": net_debt, "shares": shares, "method": s.method, "exit_margin_used": None,
           "max_entry_price": None, "multiple_price": None, "current_takeout": None, "current_irr": None,
           "target_price": None, "actionable_threshold": None, "actionable_below": None, "actionable": False, "steps": []}
    if None in (ebitda, net_debt, shares, price):
        return out
    takeout = price * (1 + s.control_premium)
    out["current_takeout"] = takeout
    if ebitda <= 0:
        out["max_entry_price"] = out["multiple_price"] = out["current_irr"] = "NM"
        return out
    out["multiple_price"] = (s.reference_multiple * ebitda - net_debt) / shares
    atp = ability_to_pay(revenue, ebitda, net_debt, shares, s)
    if atp:
        out["max_entry_price"] = atp["max_price"]
        out["current_irr"] = atp["irr_at"](takeout)
        out["exit_margin_used"] = atp["exit_margin_used"]
        out["steps"] = [["Debt raised at entry", f"{atp['debt0'] / 1e6:,.1f}"]] + [
            [f"Year {t}: revenue / EBITDA / free cash / debt",
             f"{r / 1e6:,.1f} / {e / 1e6:,.1f} / {'' if f is None else f'{f / 1e6:,.1f}'} / {d / 1e6:,.1f}"]
            for t, r, e, f, d in atp["rows"][1:]] + [
            ["Exit value", f"{atp['exit_value'] / 1e6:,.1f}"], ["Equity at exit", f"{atp['equity_exit'] / 1e6:,.1f}"],
            ["Maximum equity cheque today", f"{atp['cheque'] / 1e6:,.1f}"], ["Maximum EV", f"{atp['max_ev'] / 1e6:,.1f}"]]
    lbo, mult = out["max_entry_price"], out["multiple_price"]
    numeric = [v for v in (lbo, mult) if isinstance(v, float)]
    if s.method == "multiple":
        target = mult if isinstance(mult, float) else None
    elif s.method == "lower":
        target = min(numeric) if numeric else None
    else:
        target = lbo if isinstance(lbo, float) else None
    if target is not None:
        threshold = target * (1 + s.near_threshold)
        out.update({"target_price": target, "actionable_threshold": threshold,
                    "actionable_below": threshold / (1 + s.control_premium), "actionable": bool(takeout <= threshold)})
    return out


def rounded(result: dict) -> dict:
    out = dict(result)
    for k in ("price", "max_entry_price", "multiple_price", "current_takeout", "target_price", "actionable_threshold", "actionable_below"):
        if isinstance(out.get(k), float):
            out[k] = round_price(out[k])
    if isinstance(out.get("current_irr"), float):
        out["current_irr"] = round(out["current_irr"], 4)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ticker", required=True)
    ap.add_argument("--thesis", type=Path, default=ROOT / "thesis.md")
    ap.add_argument("--exit-margin", type=float, help="override the exit EBITDA margin (0.18 = 18%%)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    s = read_settings(args.thesis)
    if args.exit_margin is not None:
        s = replace(s, exit_margin=args.exit_margin)
    r = rounded(evaluate(args.ticker, load_market(), s))
    if args.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return
    cur = r["currency"] or ""
    print(f"{r['ticker']}  price {r['price']} {cur}  takeout {r['current_takeout']}  |  max entry price (ability to pay) "
          f"{r['max_entry_price']}  multiple price {r['multiple_price']}  IRR at takeout {r['current_irr']}")
    print(f"  target ({r['method']}) {r['target_price']}  actionable when the share is below {r['actionable_below']}  "
          f"-> {'ACTIONABLE' if r['actionable'] else 'not actionable'}")
    for label, value in r["steps"]:
        print(f"  {label:<48} {value}")


if __name__ == "__main__":
    main()
