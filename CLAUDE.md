# p2p-monitor — workshop repo (hackathon, advanced session)

A buyout monitor for listed companies, cut down to what the workshop needs. `WORKSHOP.md` is the walkthrough.

## Map
- `thesis.md` — the participant's investment thesis (filled in Part 3). Sections: 1 strategy, 2 filters (code), 3 judgment criteria (judge), 4 valuation settings (code).
- `data/` — FROZEN: `companies.csv` (30 companies, figures computed, as of 2026-10-19), `facts/<TICKER>.md`, `market.json` (prices, VWAP, financials for the code). Read-only.
- `templates/` — the two output layouts (HTML dashboard, Excel screener). Filled by code, never redrawn.
- `p2p/screen.py` — filters of thesis section 2 → `outputs/radar.csv`. Code, deterministic.
- `p2p/judge.py` — one company + thesis → Priority / Radar / Reject. The only call to a language model. Prompt: `prompts/judge_<v>.md`. `--radar` judges the whole radar into `outputs/judgments.csv`.
- `p2p/target_price.py` — ability to pay (5-year LBO) and multiple price, from `data/market.json` and thesis section 4. Code. Method: `docs/target-price.md`.
- `p2p/dashboard.py` — fills `templates/p2p_dashboard_template.html` (and the Excel screener with `--excel`) from radar + judgments + target prices → `outputs/`.
- `p2p/llm.py` — the model call (`claude -p` by default, no API key).
- `evals/` — the judge's test suite: `cases/*.json` (golden set), `run.py`, `compare.py`, `results/`, `thesis_diagnostics.md` (fixed thesis).
- `checks/run_checks.py` — acceptance checks of the workshop. `plugin/p2p/` — the plugin built in Part 3.

## Statuses
- **Reject**: a kill criterion is met (judge). Leaves the screener.
- **Radar**: fits the strategy, keep watching (judge), or not judged yet.
- **Priority**: no kill criterion and the thesis criteria are met: we would buy at the right price (judge).
- **Actionable**: Priority AND takeout price ≤ target price × (1 + near threshold). Code (`p2p/target_price.py`), never stored, only computed by the dashboard.

## Rules
1. Code calculates, the model judges. Never ask the model for a number that is in `data/`. Prices and statuses come from code.
2. `data/` and `evals/cases/` (and any `evals/cases_<sector>/`) are read-only for you (Claude). A human adds or changes a golden case, by hand, in the editor.
3. One change at a time between two eval runs: the prompt, OR the model, OR the cases. Then `evals/run.py`, then `evals/compare.py`.
4. Never edit a prompt version in place: copy `judge_vN.md` to `judge_vN+1.md`.
5. One `git commit` per eval iteration, on the participant's branch, never on `main`. Messages in English.
6. Keep the plugin sector-agnostic: company, ticker and team names belong in `thesis.md`, not in skills or hooks.
7. Standard library only. Python 3.9+. Windows and Mac. No new dependency without asking.

## Commands
- `python p2p/screen.py` · `python p2p/judge.py --ticker SBS.DE` · `python p2p/judge.py --radar` · `python p2p/dashboard.py [--excel]`
- `python p2p/judge.py --case evals/cases/003-leverage-just-above.json` · `python p2p/target_price.py --ticker SBS.DE --exit-margin 0.18`
- `python evals/run.py --prompt v1 --model haiku` · `python evals/compare.py` · `python checks/run_checks.py`
- `claude --plugin-dir ./plugin/p2p` then `/reload-plugins` after each change.
