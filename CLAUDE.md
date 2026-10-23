# p2p-monitor — workshop repo (ARCHIMED hackathon, advanced session)

A buyout monitor for listed companies, cut down to what the workshop needs. `WORKSHOP.md` is the walkthrough.

## Map
- `thesis.md` — the participant's investment thesis (filled in Part 3). Sections: 1 strategy, 2 filters, 3 judgment criteria.
- `data/` — FROZEN: `companies.csv` (30 companies, figures computed, as of 2026-10-19), `facts/<TICKER>.md`. Read-only.
- `p2p/screen.py` — filters of thesis section 2 → `outputs/radar.csv`. Code, deterministic.
- `p2p/judge.py` — one company + thesis → Fit / Watch / Reject. The only call to a language model. Prompt: `prompts/judge_<v>.md`.
- `p2p/llm.py` — the model call (`claude -p` by default, no API key).
- `evals/` — the judge's test suite: `cases/*.json` (golden set), `run.py`, `compare.py`, `results/`, `thesis_diagnostics.md` (fixed thesis).
- `checks/run_checks.py` — acceptance checks of the workshop. `plugin/p2p/` — the plugin built in Part 3.

## Rules
1. Code calculates, the model judges. Never ask the model for a number that is in `data/`.
2. `data/` and `evals/cases/` are read-only for you (Claude). A human adds or changes a golden case, by hand, in the editor.
3. One change at a time between two eval runs: the prompt, OR the model, OR the cases. Then `evals/run.py`, then `evals/compare.py`.
4. Never edit a prompt version in place: copy `judge_vN.md` to `judge_vN+1.md`.
5. One `git commit` per eval iteration, on the participant's branch, never on `main`. Messages in English.
6. Keep the plugin sector-agnostic: company, ticker and team names belong in `thesis.md`, not in skills or hooks.
7. Standard library only. Python 3.9+. Windows and Mac. No new dependency without asking.

## Commands
- `python p2p/screen.py` · `python p2p/judge.py --ticker SBS.DE` · `python p2p/judge.py --case evals/cases/003-leverage-just-above.json`
- `python evals/run.py --prompt v1 --model haiku` · `python evals/compare.py` · `python checks/run_checks.py`
- `claude --plugin-dir ./plugin/p2p` then `/reload-plugins` after each change.
