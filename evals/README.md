# Evals

The test suite of the judge. One file per case in `cases/`:
```json
{"id": "003-leverage-just-above", "title": "...", "input": {"company": {...}, "facts": "..."} | {"ticker": "QDEL"},
 "expected": "Reject", "why": "...", "tags": ["leverage", "kill"]}
```
`input.company` and `input.facts` describe a synthetic company; `input.ticker` alone loads a real one from `data/`.
Labels are set against `thesis_diagnostics.md`, the fixed eval thesis. Humans write and change cases, by hand.

- `python evals/run.py [--prompt v2] [--model sonnet] [--structured] [--label "..."]` → `results/<ts>-<model>-<prompt>.json`
- `python evals/compare.py [A B]` → gained, lost (regressions), still failing
- `results/` is committed: the CI check reads it, and the history of runs is the proof of the prompt.
