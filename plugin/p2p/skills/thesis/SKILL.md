---
name: thesis
description: Interview the user to fill in or adjust the investment thesis (thesis.md), section by section, with the Example column as default answers. Use when the user wants to set up, change or review their investment thesis, screening filters, judgment criteria or valuation settings ("set up my thesis", "change the market cap ceiling", "add a country", "update my kill criteria").
argument-hint: "[section number to jump to, e.g. 2]"
allowed-tools: Read, Edit, Bash(python p2p/*.py *)
---

# Thesis interview

You help the user fill in `thesis.md` at the repo root by asking questions. The user decides every answer; you only
write what they said into the file.

## Rules
- Read the defaults from `thesis.md` itself: the **Example** column (sections 2 and 3), the *Example* quote (section 1)
  and the **Default** column (section 4). Never invent a default, never assume a sector.
- Ask **3 to 5 questions at a time**, one section at a time. Show each default next to its question so the user can
  answer "keep", "default" or give a new value.
- If the user already has values in **Your value / Your rule / Min / Max**, show those as the current answer instead of
  the example, and ask only what they want to change.
- Never compute a number yourself. Write numbers exactly as the user gave them, in the format the table expects.
- Edit only the answer cells: **Your answer** (section 1), **Min**, **Max**, **Your value** (section 2), **Your rule**
  (section 3), **Your value** (section 4). Never change headings, the Field, Example, Effect or Default columns, or the
  intro text: the code parses this file.
- Never put a `|` character inside a table cell.
- Do not touch `evals/thesis_*.md`: those are fixed copies for the tests.

## Steps
1. Read `thesis.md`. If an argument names a section, start there. Otherwise tell the user in one line which sections
   are already filled in and which are empty, then start with the first empty one.
2. **Section 1, strategy.** Show the example and ask for 3 to 5 lines in their words (or "keep the example"). Write it
   after `> **Your answer:**`.
3. **Section 2, filters.** Ask about the rows of the table, 3 to 5 at a time. Format rules for the code:
   - Lists (team, countries, role) go in **Your value**, comma-separated, spelled exactly as in `data/companies.csv`
     (check the file if the user's spelling may differ).
   - Ranges go in **Min** and **Max** as plain numbers: market cap in € millions (`100`, `4000`), margin as a fraction
     (`0.10` for 10%). Leave a cell blank to switch that bound off.
4. **Section 3, judgment criteria.** Ask for each rule, 3 to 5 at a time, offering the example. Remind the user that
   the **Effect** column is fixed: it says what the judge does when the rule fails. Write their rule in **Your rule**.
   For the Verdict row, "keep" means writing `keep` in **Your rule**.
5. **Section 4, valuation.** Ask whether they want to change any setting. Show the defaults as a short list and only
   ask about the ones they want to change. Write values in the same format as the Default column (`13x`, `25%`, `5`).
   Blank or `default` keeps the default.
6. After each section, write the answers into `thesis.md`, then show the user what you wrote in a short table before
   moving to the next section.
7. At the end, summarise what changed in a few lines. If section 2 changed, offer to run
   `python p2p/screen.py` and show how many companies pass and which filter excluded the others.
