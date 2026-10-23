# data/ (frozen, read-only)

- `companies.csv`: 30 listed healthcare companies, 8 teams, as of 2026-10-19. Figures already computed by code:
  `market_cap_eur_m`, `ev_eur_m`, `revenue_ltm_eur_m`, `ebitda_margin_ltm`, `net_debt_to_ebitda` (= (total debt − cash) / EBITDA, TTM),
  `price_change_3m`, `price_change_12m`, `held_pct_insiders`, `top_holder`, `top_holder_pct`. Blank = unknown.
- `market.json`: for the code only: last close, 90-day VWAP, 1D / 1W / YTD changes, six months of daily closes, market cap, EV, TTM revenue, EBITDA, debt, cash, shares. `p2p/target_price.py` and `p2p/dashboard.py` read it.
- `facts/<TICKER>.md`: what the dataset knows about one company, in words, with sources. What it does not know is listed too.

Source: Yahoo Finance via yfinance 1.7.0, frozen for the workshop (`p2p_frozen_dataset.xlsx` of the starter kit).
Nothing here is written by code or by Claude: the hook of Part 3 enforces it.
