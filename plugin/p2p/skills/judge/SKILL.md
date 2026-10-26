---
name: judge
description: Judge whether a listed company fits the investment thesis (Priority, Radar or Reject) with the tested judge, then let the user confirm or override the verdict and refresh the dashboard. Use when the user asks "does <company> fit my thesis?", "should we look at <ticker>?", "judge <company>", "is <company> a target?", or wants the whole radar judged.
argument-hint: "<ticker or company name> | radar"
allowed-tools: Bash(python p2p/*.py *), Bash(PYTHONIOENCODING=utf-8 python p2p/*.py *), Read, Edit
---

# Judge a company against the thesis

You never judge a company yourself. The verdict comes from `p2p/judge.py`, which runs the prompt tested by the evals.
Your job: run it, explain the result in plain language, record the user's final decision, refresh the dashboard.

## Rules
- Never give your own verdict, and never change the judge's `verdict`. Only the user may override, in `final_verdict`.
- Never compute a number (leverage, margins, prices). Quote figures only as the script or `data/` gives them.
- The thesis is `thesis.md` at the repo root. If its sections 1 to 3 are empty, stop and suggest `/p2p:thesis` first.
- Prefix every script call with `PYTHONIOENCODING=utf-8` (Windows consoles otherwise crash on some characters).

## Steps
1. **Pick the prompt.** Read the `summary` of the most recent file in `evals/results/` whose accuracy is at least 0.8,
   and use its `prompt` and `model`. If there is none, use `v1` and `haiku` and say the judge is untested. Tell the user
   in one line which prompt and model you use and their eval score.
2. **Find the company.** If the user gave a name, find its ticker in `data/companies.csv`. If the user asked for the
   radar, skip to step 6. If the company is not in `outputs/radar.csv` (run `python p2p/screen.py` if that file is
   missing), say which filter excludes it (`outputs/radar_excluded.csv`) and ask whether to judge it anyway.
3. **Run the judge:**
   `PYTHONIOENCODING=utf-8 python p2p/judge.py --ticker <TICKER> --prompt <prompt> --model <model> --json`
4. **Present the result** in plain language, short:
   - the verdict, in bold, and what it means (Priority: we would buy at the right price; Radar: keep watching;
     Reject: a kill criterion is met);
   - the reasons, as a short list;
   - the missing facts, if any: what someone should find out to move the verdict;
   - if the verdict is `ParseError` or `Error`, say so and show the error; do not record it.
5. **Ask the user to confirm or override:** keep the verdict, or choose Priority, Radar or Reject, with a one-line
   reason if they override. Then update `outputs/judgments.csv` (columns
   `ticker,verdict,final_verdict,judged_on,prompt,model,note`): replace the row of that ticker, or add it. `verdict` is
   the judge's, `final_verdict` is the user's decision, `judged_on` is today (YYYY-MM-DD), `note` is the first reason
   (or "Override: <user's reason>" if overridden), at most 300 characters, without commas breaking the CSV (quote it).
6. **Radar mode:** run `PYTHONIOENCODING=utf-8 python p2p/judge.py --radar --prompt <prompt> --model <model>`, which
   writes `outputs/judgments.csv` itself. Show the verdicts as a table, then ask whether the user wants to override
   any; for each override, edit only that row's `final_verdict` and `note`.
7. **Refresh the dashboard:** `PYTHONIOENCODING=utf-8 python p2p/dashboard.py`, and tell the user the file to open
   (`outputs/p2p_dashboard.html`) and the company's status there (Radar, Priority, or Priority actionable).
