# p2p-monitor

A buyout monitor for listed companies ("P2P", public-to-private), reduced to its judgment brick, for a 2 h 30 workshop
on two things: **how you prove that a language-model feature works (evals)**, and **how you package expertise for
Claude Code (a plugin: skills and hooks)**. The walkthrough is in [`WORKSHOP.md`](WORKSHOP.md).

## Before you start (5 minutes, the day before)
1. `python --version` → 3.9 or later (`python3` on Mac). Nothing to install: standard library only.
2. `git --version` and access to this repository.
3. Claude Code installed and logged in: `claude -p "say pong" --output-format json` must print a JSON answer.
   (`p2p/llm.py` calls the model through Claude Code: no API key needed.)

## See it work
```
git clone <this repo> && cd p2p-monitor
git switch -c hackathon/<your-name>
python p2p/screen.py --thesis evals/thesis_diagnostics.md      # the radar, from the Diagnostics example thesis
python p2p/judge.py --radar --thesis evals/thesis_diagnostics.md   # the model judges the radar companies
python p2p/dashboard.py --thesis evals/thesis_diagnostics.md    # the dashboard: open outputs/p2p_dashboard.html
python evals/run.py                                             # the whole test suite of the judge
```

Four statuses: **Reject** (a kill criterion, judge), **Radar** (fits the strategy, keep watching, judge), **Priority** (we
would buy at the right price, judge), **Actionable** (Priority and the price is right: code, from the target price).

## What is where
| | |
|---|---|
| `thesis.md` | your investment thesis (strategy, filters, judgment criteria, valuation settings) |
| `data/` | frozen data: 30 companies, facts files. Read-only |
| `p2p/` | `screen.py` (filters, code), `judge.py` (the model), `target_price.py` (code), `dashboard.py` (fills the templates), `llm.py` (the call) |
| `templates/` | the HTML dashboard and the Excel screener layouts, filled by `dashboard.py` |
| `docs/` | architecture, the target-price method with its worked example |
| `prompts/` | the judge's system prompt, one file per version |
| `evals/` | golden cases, runner, comparison, results, the fixed eval thesis |
| `checks/` | acceptance checks: `python checks/run_checks.py` |
| `plugin/p2p/` | the plugin you build (Part 3) |
| `.github/workflows/` | what a CI would run on each pull request (illustration) |

Data: Yahoo Finance via yfinance, frozen on 2026-10-19, for 30 companies tagged to 8 healthcare teams. Offline.
