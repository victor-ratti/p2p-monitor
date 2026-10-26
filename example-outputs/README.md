# example-outputs/

A **snapshot** of `outputs/` at the end of a successful workshop run, kept so you can see what the finished chain
produces. No code reads these files: editing them changes nothing. Your own run writes to `outputs/` (ignored by git).

Produced with:
- Thesis: `thesis.md` (Healthcare IT, filled in with `/p2p:thesis`), data as of 2026-10-19
- Judge: prompt `v2`, model `haiku` (16/16 on the golden set, `evals/results/`)

| File | Written by | Content |
|---|---|---|
| `radar.csv` / `radar_excluded.csv` | `p2p/screen.py` | companies passing the filters / the others, with the filter that excluded them |
| `judgments.csv` | `p2p/judge.py --radar` | verdict per radar company; `final_verdict` is the one a person confirmed or overrode |
| `screener.csv` / `p2p_dashboard.html` | `p2p/dashboard.py` | statuses, target prices, takeout price and IRR |

Regenerate: `python p2p/screen.py`, `python p2p/judge.py --radar --prompt v2`, `python p2p/dashboard.py`.
