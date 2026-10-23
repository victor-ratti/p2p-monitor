# Architecture

```
thesis.md ──section 2──> p2p/screen.py ──> outputs/radar.csv            (code: deterministic)
thesis.md ──sections 1,3──┐
data/companies.csv + facts/ ──┴──> p2p/judge.py ──> {verdict, reasons, missing_facts}   (model, via p2p/llm.py)
                                       ▲
evals/cases/*.json + evals/thesis_diagnostics.md ──> evals/run.py ──> evals/results/*.json ──> evals/compare.py
outputs/judgments.csv + data/market.json + thesis §4 ──> p2p/target_price.py ──> p2p/dashboard.py ──> outputs/p2p_dashboard.html, screener.csv, p2p_screener.xlsx
plugin/p2p: skills (thesis, judge) call the scripts; hooks/protect_golden.py guards data/ and evals/cases/
```
Statuses: Reject, Radar, Priority come from the judge (model); Actionable = Priority and takeout ≤ target price (code).
- The model is called in exactly one place (`p2p/llm.py`), through the Claude Code CLI (`claude -p`) or the Anthropic SDK.
- The judge is evaluated against a FIXED thesis (`evals/thesis_diagnostics.md`), so the golden labels stay valid whatever
  the participant writes in `thesis.md`.
- Nothing here is deployed: deployment, authentication and CI ownership belong to the IT team.
