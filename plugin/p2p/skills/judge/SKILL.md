---
name: judge
description: Judge whether a company (by name or ticker) or the whole radar fits the thesis, present the verdict, reasons and missing facts, let the user confirm or override, record the decision and refresh the dashboard. Use when the user asks "does <company> fit my thesis?", wants a company judged, or wants the radar judged.
allowed-tools: Read Edit Bash(python p2p/*.py *)
---

# Judge

You do not judge by yourself. The tested prompt does, through `p2p/judge.py`: it is the only place where a model decides, and the quality proved by the evals carries over only if you call it. Never give your own verdict, never compute a number, never read the thesis to decide.

## Settings
Use the prompt version and model of the best run in `evals/results/` (default: `--prompt v4 --model sonnet`). Say which ones you used. Use the thesis `thesis.md` (the default).

## One company
1. Resolve the company to a ticker with `data/companies.csv` (Read it, match name or ticker). If it is not in the file, say so and stop. If several match, ask which.
2. Run `python p2p/judge.py --ticker <TICKER> --prompt <v> --model <m> --json`.
3. Present, in plain language and short:
   - the verdict (**Priority**, **Radar** or **Reject**) in the first line;
   - the reasons, as the judge gave them;
   - the missing facts, if any. An unknown fact is never a pass: say so when it drives the verdict.
   - If the run reports a parse error, say so and offer to run it again. Do not invent a verdict.
4. Ask the user to **confirm** the verdict or **override** it with another (Priority, Radar or Reject). If they override, ask for a one-line reason.
5. Record the decision in `outputs/judgments.csv` (columns: `ticker,verdict,final_verdict,judged_on,prompt,model,note`):
   - `verdict` is always the judge's own answer; `final_verdict` is the user's decision.
   - If the ticker has a row, edit that row in place (replace its `final_verdict`, and update `verdict`, `judged_on`, `prompt`, `model` and `note` from this run). Otherwise append a row, with today's date, a note of at most 300 characters (the first reason; add "override: <reason>" when overridden) and quotes around the note if it contains a comma.
   - If the file does not exist, create it with the header first.
6. Run `python p2p/dashboard.py` and tell the user where the output is.

## The whole radar
1. If `outputs/radar.csv` does not exist, run `python p2p/screen.py` first.
2. Run `python p2p/judge.py --radar --prompt <v> --model <m>`. It writes `outputs/judgments.csv` with `final_verdict` equal to the judge's verdict.
3. Show a table: ticker, verdict, one-line reason. Group by verdict, Priority first.
4. Ask which verdicts the user wants to override (none is fine). For each override, ask the new verdict and a one-line reason, then edit only the `final_verdict` of that row.
5. Run `python p2p/dashboard.py`.

## Rules
- Never edit `data/`, `evals/` or `prompts/`.
- Never change `verdict`, the judge's own answer, when recording an override: only `final_verdict`.
- Actionable is not a verdict: the dashboard computes it from Priority and the target price. Never write it in the CSV.
- Name no sector, team or company in this skill; take them from the data and the thesis at run time.
