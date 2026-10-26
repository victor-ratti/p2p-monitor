# Target price: how the system decides what the fund can pay

Your settings live in `thesis.md` (section 4); the calculation is done in code, never by Claude in the chat.

## The idea in four lines
- A **Priority** company is one we would buy at a **target price** per share.
- Buying a listed company means paying the share price **plus a control premium** (shareholders must be paid to sell): that is the **takeout price**.
- The company becomes **Actionable** when the takeout price is close to or below the target price.
- There are two ways to set the target price: **multiples** or **ability to pay** (5-year LBO, 25% target IRR). The system computes both; your thesis chooses which one triggers the alert (default: ability to pay).

## Method 1: multiples ("what is it worth?")
Companies in a sector tend to trade at a similar multiple of EBITDA. Value the company at that multiple:

```
multiple price = (reference multiple × EBITDA − net debt) / shares
```

Tells you if the company is cheap versus peers. Does not tell you if the fund can earn its return.

## Method 2: ability to pay ("the most we can pay and still earn our target return")
The fund buys with its own money (equity) plus a bank loan (debt), holds 5 years, then sells. A 25% IRR over 5 years means getting back **1.25⁵ ≈ 3.05×** the equity put in. Work backwards from the exit:

| # | Step | Formula |
|---|---|---|
| 1 | Debt raised at entry | leverage × EBITDA today |
| 2 | Each year | revenue grows; margin moves in a straight line to the exit margin; free cash = cash conversion × EBITDA − interest on debt; free cash repays debt |
| 3 | Value at exit (year 5) | exit multiple × year-5 EBITDA |
| 4 | Equity at exit | exit value − debt left (+ any cash left) |
| 5 | Maximum equity cheque today | equity at exit / (1 + target IRR)^years |
| 6 | Maximum price for the whole company (EV) | (equity cheque + debt raised) / (1 + fees) |
| 7 | **Maximum price per share** | (maximum EV − current net debt) / shares |

Debt is sized on EBITDA and the exit multiple is a fixed number, so the maximum price comes out directly: no trial and error.

**IRR at a given price** (for the "Current IRR" column): equity cheque = (price × shares + net debt) × (1 + fees) − debt raised; IRR = (equity at exit / equity cheque)^(1/years) − 1.

## From target price to status
```
target price  = the method in thesis.md section 4: lbo | multiple | lower (of the two)
takeout price = share price (premium basis) × (1 + control premium)
Actionable    = Priority and takeout price ≤ target price × (1 + near threshold)
```
Negative or zero EBITDA: both methods are "NM" (not meaningful) and the company cannot become Actionable.

## Worked example: Stratec (Diagnostics), frozen data as of 2026-10-19
Inputs (EUR millions, from `data/market.json`, ticker `SBS.DE`): revenue = `revenue_ttm` 244.809; EBITDA = `ebitda_ttm` 28.325, margin 11.6%; net debt = `total_debt` 115.720 − `total_cash` 19.033 = 96.687; shares = `shares_outstanding` 12.155942M; price = `price` €23.65.

Settings (example values, not the fund's house view): reference multiple 13x; target IRR 25%; 5 years; leverage 4.0x; exit multiple 12x; revenue growth 5%; **exit margin 18%** (Stratec's FY2024 EBITDA margin was 18.4%: the thesis is a margin recovery); cash conversion 50%; interest 7.5%; fees 3%; control premium 30% on last close; near threshold 5%.

| Year | Revenue | EBITDA | Free cash | Debt at year end |
|---|---|---|---|---|
| 0 | 244.8 | 28.3 | | 113.3 |
| 1 | 257.0 | 33.0 | 8.0 | 105.3 |
| 2 | 269.9 | 38.2 | 11.2 | 94.1 |
| 3 | 283.4 | 43.7 | 14.8 | 79.3 |
| 4 | 297.6 | 49.7 | 18.9 | 60.4 |
| 5 | 312.4 | 56.2 | 23.6 | 36.8 |

| Result | Value |
|---|---|
| Exit value (12 × 56.2) | 674.9 |
| Equity at exit | 638.1 |
| Maximum equity cheque (638.1 / 3.05) | 209.1 |
| Maximum EV ((209.1 + 113.3) / 1.03) | 313.0 |
| **Maximum price per share (ability to pay)** | **€17.80** |
| Multiple price (13 × 28.3 − 96.7) / 12.156 | €22.34 |
| Takeout today (23.65 × 1.30) | €30.75 |
| IRR if we paid the takeout today | 11.4% |
| Status today | Not Actionable (30.75 > 17.80 × 1.05 = 18.69) |
| Share price that makes it Actionable | ≤ €14.37 (a ~39% drop) |

Reproduce it: `python p2p/target_price.py --ticker SBS.DE --exit-margin 0.18` (the other settings are the defaults).

## Simulations (stretch goal)
Pick one of your Priority companies. Ask Claude to create a **SYNTHETIC** price series that falls to just below the price that makes it Actionable, computed by your code from your own target price. Label it SYNTHETIC everywhere it appears. With the example settings, Stratec at €14.00 gives a takeout of €18.20 ≤ €18.69: Actionable.

## What this simple model leaves out (say so if asked)
Taxes and capex are inside "cash conversion"; one debt tranche; no management package; no dividends. Good enough to rank and alert; the deal team runs the full model once a company is Actionable.
