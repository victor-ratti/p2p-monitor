---
name: thesis
description: Interview the user section by section and fill in thesis.md (strategy, screening filters, judgment criteria, valuation settings). Use when the user wants to create, adjust or review the investment thesis, a filter, a criterion or a valuation setting.
allowed-tools: Read Edit Bash(python p2p/screen.py)
---

# Thesis interview

Goal: fill in `thesis.md` by asking questions, so nobody has to edit tables by hand.
Never write a sector, team or company name in this skill: every default comes from the **Example** column of `thesis.md`, read at run time.

## Before you start
1. Read `thesis.md`. If `outputs/radar.csv` exists, note how many companies it holds (the "before" count).
2. Ask which sections to cover (1 to 4, default: all, in order). If a section already has values in **Your answer / Your value / Your rule / Min / Max**, show them and ask whether to keep or change them.

## How to ask
- Section by section, **3 to 5 questions at a time**, never the whole table at once.
- For each question, quote the relevant **Example** from the file as the proposed default and say "reply `ok` to accept it, or give your own value; reply `skip` to leave it blank".
- Questions use plain business words (the "Filter", "Criterion" or "Setting" column), not field names.
- Section 1: ask for the strategy in 3 to 5 lines (what kind of listed company, why better off privately); default is the Example.
- Section 2: per filter ask for the Min, Max or list. Margins are fractions (0.10 = 10%). Lists use names exactly as in the data. Blank means the filter is off.
- Section 3: one question per criterion, asking for a rule a colleague could apply without the user. Leave the **Effect** and **Example** columns untouched. For the Verdict row, ask only "keep or rewrite".
- Section 4: ask only about the settings the user wants to change; blank or `default` keeps the default. Never compute a price here.
- Accept `ok` literally as the Example text (for section 2, copy the Example's numbers into Min/Max or the list into Your value).

## Writing
- After each batch of answers, edit `thesis.md` in place with Edit: fill only the **Your answer / Your value / Your rule / Min / Max** cells. Never change headings, columns, Example or Effect text.
- Keep the Markdown tables aligned in structure (same number of `|` per row).
- Do not touch `data/`, `evals/` or `prompts/`.

## Closing
1. Show a short recap of what changed (section, field, old → new).
2. If any section 2 filter changed, run `python p2p/screen.py` and report the radar count before → after, and name a few companies that entered or left if the output shows them. Suggest the user undo with the old value if the result is empty.
3. Remind them that section 3 changes only affect the judge (re-run the evals before trusting a changed criterion) and section 4 changes only affect target prices.
