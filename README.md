# p2p-monitor

A buyout monitor for listed companies ("P2P", public-to-private), reduced to its judgment brick, for a 2 h 30 workshop
on two things: **how you prove that a language-model feature works (evals)**, and **how you package expertise for
Claude Code (a plugin: skills and hooks)**. The walkthrough is in [`WORKSHOP.md`](WORKSHOP.md).

## Before you start (5 minutes, the day before)
1. `python --version` → 3.9 or later (`python3` on Mac). Nothing to install: standard library only.
2. `git --version` and access to this repository.
3. Claude Code installed and logged in: `claude -p "say pong" --output-format json` must print a JSON answer.
   (`p2p/llm.py` calls the model through Claude Code: no API key needed.)

## Three commands to see it work
```
git clone <this repo> && cd p2p-monitor
git switch -c hackathon/<your-name>
python p2p/screen.py --thesis evals/thesis_diagnostics.md      # the radar, from the Diagnostics example thesis
python p2p/judge.py --case evals/cases/003-leverage-just-above.json   # one judgment
python evals/run.py                                             # the whole test suite of the judge
```

## What is where
| | |
|---|---|
| `thesis.md` | your investment thesis (strategy, filters, judgment criteria) |
| `data/` | frozen data: 30 companies, facts files. Read-only |
| `p2p/` | `screen.py` (code), `judge.py` (the model), `llm.py` (the call) |
| `prompts/` | the judge's system prompt, one file per version |
| `evals/` | golden cases, runner, comparison, results, the fixed eval thesis |
| `checks/` | acceptance checks: `python checks/run_checks.py` |
| `plugin/p2p/` | the plugin you build (Part 3) |
| `.github/workflows/` | what a CI would run on each pull request (illustration) |

Data: Yahoo Finance via yfinance, frozen on 2026-10-19, for 30 companies tagged to 8 healthcare teams. Offline.
