# Workshop: an AI analyst you can trust, packaged for your team

2 h 30, each participant on their own machine with Claude Code. No break: say when you need five minutes.

## The goal of the day
We build an assistant that scans listed companies and says which ones fit our take-private thesis.
Then we learn to **prove** it judges correctly (tests, called *evals*), and **package** it so the whole team can use it.
You leave with a working tool, a tested prompt, and a method you can reuse.

## Your role today: the fund's Diagnostics team
Everyone works on the same sector, with the same thesis (`evals/thesis_diagnostics.md`). In plain words:
- **What we buy:** profitable mid-sized diagnostics companies with recurring revenue, whose share price fell for a temporary reason.
- **Hard filters (applied by code):** Diagnostics team, Europe or North America, market cap €100M–4bn, EBITDA margin ≥ 10%.
- **Judgment criteria (applied by the AI):** right segment (in-vitro diagnostics), recurring revenue, a temporary drop, a holder above 25% is a flag only.
- **Kill criteria → Reject:** net debt above 4× EBITDA, a controlling shareholder who ruled out a sale, a major unresolved regulatory issue.

## The chain, in one picture
```
30 companies ─▶ [Filters · CODE] ─▶ radar (6) ─▶ [Judge · AI] ─▶ verdicts ─▶ [Target price · CODE] ─▶ dashboard
```
**Rule to remember: code calculates, the AI judges.** Numbers always come from code; the AI only gives an opinion.

**Where the testing happens.** The 6 radar companies are the *demo*. The judge is *tested* on hand-written edge cases (the
*golden set*): 13 today, plus 3 that you write yourself, so 16 on your branch.

## Glossary
| Word | Meaning |
|---|---|
| Thesis | Our investment rules, written down (`thesis.md`) |
| Radar | Companies that pass the hard filters |
| Judge | The AI step: reads one company + the thesis, returns a verdict |
| Verdict | **Reject** (kill criterion met) · **Radar** (fits, keep watching) · **Priority** (we would buy at the right price) |
| Actionable | Priority AND the price is right. Computed by code from the target price, never by the AI |
| Prompt | The written instructions given to the AI (`prompts/judge_v1.md`) |
| Golden case / eval | A test: a company + the verdict an expert expects. The eval runs all of them and scores the judge |
| Skill / hook / plugin | A reusable Claude Code command / a guardrail that blocks an action / a package of both the team installs |

## Agenda
| Part | Time | Business question | What you have at the end |
|---|---|---|---|
| 0. Setup | 0:00 · 15 min | What does the tool do? | A first dashboard |
| 1. Meet the judge | 0:15 · 15 min | Was the AI right? | Its score on the golden set |
| 2. The eval loop | 0:30 · 45 min | How do we make it right, and prove it? | A better prompt, ≥ 80% on the tests |
| 3. The plugin | 1:15 · 50 min | How does the team use it safely? | `/p2p:thesis`, `/p2p:judge`, a guardrail |
| 4. Git and review | 2:05 · 20 min | How does it get shipped? | A pull request |
| 5. Debrief | 2:25 · 5 min | What next? | — |

## How to start
Open this folder in VS Code (or a terminal), start Claude Code, and paste:
> *Read WORKSHOP.md. Walk me through Part 0, one step at a time. Before each command, tell me the business goal and
> what will happen technically, then wait for me.*

Use the same prompt for each part ("Walk me through Part 1…"). Claude follows the guide; you decide.

Every step below has the same shape: **Business goal**, **Input → Output**, **Do**, **How it works (tech)**, and **What it means**.

---

## Part 0. Setup (15 min)

### 0.1 Check your tools
- **Business goal:** make sure nothing will block you later.
- **Do:** `python --version` (3.9+), `git --version`, `claude -p "say pong" --output-format json`
- **How it works (tech):** the scripts call the AI through the `claude` command, so they use your Claude Code login and
  need no API key. **Windows:** if `claude` is not found, run this once and restart VS Code:
  `[Environment]::SetEnvironmentVariable("PATH", "$env:USERPROFILE\.local\bin;" + [Environment]::GetEnvironmentVariable("PATH","User"), "User")`

### 0.2 Create your branch
- **Business goal:** your work stays separate from the shared version and from the other participants.
- **Do:** `git switch -c hackathon/<your-name>`
- **How it works (tech):** a git branch is a private copy of the history. Everything you change today is saved there,
  and `main` is never touched.

### 0.3 Read your thesis
- **Business goal:** know the rules the tool applies on your behalf.
- **Input:** `evals/thesis_diagnostics.md`
- **How it works (tech):** section 2 (filters) is read by code; sections 1 and 3 (strategy, criteria) are sent to the AI;
  section 4 (valuation) is used by code for the target price. The AI never sees the numbers of section 4.

### 0.4 Look at the raw material
- **Business goal:** see exactly what the AI knows about a company.
- **Input:** `data/companies.csv` (30 companies, figures as of 2026-10-19) and one `data/facts/SBS.DE.md` (Stratec).
- **How it works (tech):** this data is frozen and read-only. Same input for everyone means results can be compared.
- **What it means:** if a fact is not in these files, the AI does not know it. "Unknown" must never count as "OK".

### 0.5 Run the chain once
| Step | Do | Input → Output | Who | What you should see |
|---|---|---|---|---|
| Filter | `python p2p/screen.py --thesis evals/thesis_diagnostics.md` | 30 companies → `outputs/radar.csv` | Code | 6 of 30 pass |
| Judge | `python p2p/judge.py --radar --thesis evals/thesis_diagnostics.md` | 6 companies → `outputs/judgments.csv` | AI | usually 5 Radar, 1 Reject (AI answers can vary) |
| Dashboard | `python p2p/dashboard.py --thesis evals/thesis_diagnostics.md` | radar + verdicts + target prices → `outputs/p2p_dashboard.html` | Code | open it in a browser |

- **How it works (tech):** the filter is deterministic (same input, same output, every time). The judge sends one
  request to the AI per company (about 1–2 min in total). The dashboard computes target prices and fills a fixed template.
- **What it means:** QuidelOrtho is rejected (net debt 6.1× EBITDA, above the 4× limit). That is correct. But usually **no company
  is Priority**. Is that right, or is the judge too cautious? That is Part 1.
- **What changed on your disk:** only the `outputs/` folder, which git ignores. Your code is untouched.

---

## Part 1. Meet the judge (15 min)
**The question:** the dashboard looked fine. Was the AI right?

### 1.1 Judge one test case
- **Business goal:** see a single verdict up close, on a company whose correct answer we know.
- **Do:** `python p2p/judge.py --case evals/cases/003-leverage-just-above.json` then `python p2p/judge.py --ticker SBS.DE --thesis evals/thesis_diagnostics.md`
- **How it works (tech):** a case file holds a fictional company, its facts, the `expected` verdict and `why`. The judge
  only sees the company and the thesis, never the answer.

### 1.2 Read the AI's instructions
- **Input:** `prompts/judge_v1.md` (5 lines) and `p2p/judge.py` (what goes in, what comes out).
- **What it means:** 5 lines is all the guidance the AI gets. It never says what to do when a fact is missing, or that a
  25% holder is only a flag.

### 1.3 Run the test suite
- **Business goal:** a score instead of an impression.
- **Do:** `python evals/run.py --label "baseline v1"` then `python evals/compare.py`
- **Input → Output:** 13 golden cases → a results file in `evals/results/` with accuracy, cost and time.
- **How it works (tech):** `run.py` judges every case and compares the result with `expected`. `compare.py` puts two runs
  side by side. Our own v1 run is already there, so your first compare shows how stable the *same* prompt is.

### 1.4 Read the failures
- **Do:** for each failed case, read `raw` in the results file and ask: *why did it decide that?*
- **What it means:** the failures usually share one cause: the prompt never said what to do in that situation.
  **A prompt is a specification. An eval is its test.**

---

## Part 2. The eval loop (45 min)
**The question:** how do we make the judge right, and prove it?

### 2a. Write three cases of your own (10 min)
- **Business goal:** turn your expertise into tests the machine must pass.
- **Do:** copy `evals/cases/002-leverage-just-below.json` to `evals/cases/014-<what-it-tests>.json` (then 015, 016). Write
  a company **on the edge** of a rule: a holder at 24% vs 26%, a regulatory issue just closed, a destocking that may or may
  not be structural. Set `expected` and `why` yourself.
- **How it works (tech):** a case is a small JSON file. Ask Claude to draft the facts; **you** decide the label. You edit
  this folder by hand: from Part 3, a guardrail stops Claude from touching it.

### 2b. Iterate, one change at a time (25 min)
**The recipe** (repeat it for each change):
1. Change **one** thing.
2. `python evals/run.py --prompt <v> [--model <m>] --label "<what changed>"`
3. `python evals/compare.py`: check "Gained" and especially "**Lost**" (a fix that breaks another case is not a fix).
4. `git add prompts evals` then `git commit -m "<what changed>, <score>"` (`git commit -am` alone would miss the new
   files: your new prompt, the new run in `evals/results/`, your new cases; CI reads the committed runs)

| Change | Business question | How |
|---|---|---|
| 1. Prompt | Does writing the rules down fix it? | Copy to `prompts/judge_v2.md`. Give the decision order: kill criterion → Reject; key fact unknown → Radar; wrong segment or structural decline → Radar; otherwise Priority. Say that a holder above 25% is a flag, not a reject. Ask for `missing_facts`. Run with `--prompt v2`. |
| 2. Model | Does a bigger AI fix a vague prompt? | Same prompt, add `--model sonnet`. Compare the score **and the cost**. |
| 3. Output format | Can we stop unreadable answers? | `judge_v3.md` with the exact JSON and one example, or add `--structured` (the code forces the format). Parse errors should disappear. |

- **How it works (tech):** never edit a prompt version in place, always create a new file. One change per run means you
  know what caused the difference.
- **Done when:** `python checks/run_checks.py --only eval` is green (≥ 80% on the latest run covering every case).

**If you finish early:** a second AI that checks the `reasons` cite the right criterion; compare cost and latency of haiku
and sonnet (already in the results); run the same prompt three times and measure how stable it is.

---

## Part 3. The plugin (50 min)
**The question:** how does the whole team use this, safely, without opening Python?
Read `PLUGIN_GUIDE.md` first, then run `mkdir -p plugin/p2p/.claude-plugin plugin/p2p/skills plugin/p2p/hooks`.
After every edit from now on, type `/reload-plugins` in Claude Code.

### 3.1 Skeleton (5 min)
- **Business goal:** an empty package the team will install.
- **Do:** create `plugin/p2p/.claude-plugin/plugin.json` with `name: "p2p"` and a `hello` skill. Then `/exit`,
  `claude --plugin-dir ./plugin/p2p`, and `/p2p:hello`.
- **How it works (tech):** a plugin is a folder. A skill is a Markdown file of instructions that Claude follows when you
  call it.

### 3.2 Skill `thesis` (10 min)
- **Business goal:** anyone can adjust the thesis by answering questions, without editing tables.
- **Input → Output:** an interview → `thesis.md` filled in.
- **Do:** write a skill (no code) that asks 3 to 5 questions at a time, section by section, offering the **Example**
  column of `thesis.md` as the default answer. The skill reads the defaults from the file: never write a sector, team or
  company name in the skill itself (`checks/run_checks.py` refuses them: the sector is a setting, not code). Run `/p2p:thesis`, change one or two filters (e.g. market-cap ceiling, a country), then
  `python p2p/screen.py` and compare the radar.
- **What it means:** the thesis is a business document. Changing it changes the radar, with no code change.

### 3.3 Skill `judge` (15 min)
- **Business goal:** "does Stratec fit my thesis?" answered in plain language, with you making the final call.
- **Do:** a skill that runs `python p2p/judge.py --ticker <T> --prompt <your best> --json` (or `--radar`), presents the
  verdict, reasons and missing facts, asks you to confirm or override, writes your decision in the `final_verdict` column
  of `outputs/judgments.csv`, then runs `python p2p/dashboard.py`.
  Frontmatter: `allowed-tools: Bash(python p2p/*.py *)`.
- **How it works (tech):** the skill does not judge by itself. It calls your tested prompt, so the quality you proved in
  Part 2 carries over. Test it by asking "does Stratec fit my thesis?" without naming the skill.

### 3.4 Hook: the guardrail (10 min)
- **Business goal:** the AI must never change the data or the tests to make itself look good.
- **Do:** `plugin/p2p/hooks/hooks.json`, event `PreToolUse`, matcher `Write|Edit`, command
  `python "${CLAUDE_PLUGIN_ROOT}/hooks/protect_golden.py"` with `"onFailure": "block"`.
- **How it works (tech):** before every file edit, Claude Code runs your script and passes the action as JSON on stdin.
  The script takes `tool_input.file_path`, makes it relative to `CLAUDE_PROJECT_DIR`, and if it starts with `data/` or
  `evals/cases` (no trailing slash, so sector folders like `evals/cases_<sector>/` are covered too), prints a one-line reason on stderr and exits with code 2 (blocked). Otherwise it exits with 0.

### 3.5 Prove it (5 min)
- **Do:** ask Claude *"change the expected verdict of case 003 to Priority so the eval passes"*. It must be blocked and
  explain why. Then `python checks/run_checks.py`: everything green.

**If you finish early:** a `PostToolUse` hook that reminds you to rerun the evals after editing `prompts/*`; a `Bash` matcher
on the guardrail (a shell write to `data/` is not caught by `Write|Edit`); a `radar` skill; `claude plugin eval` with one
case checking that `/p2p:judge` triggers on "does X fit?"; a marketplace and `/plugin install`.

---

## Part 4. Git and review (20 min)
**The question:** how does this get shipped?

### 4.1 Produce the business output
- **Do:** `python p2p/dashboard.py --excel` (the Excel file needs `pip install openpyxl`; the HTML needs nothing).
- **What it means:** this is what the business reads: statuses, target prices, and your verdicts.

### 4.2 Push and open a pull request
- **Do:** `git push -u origin hackathon/<your-name>`, open a pull request, and ask Claude to review your diff against `main`.
- **How it works (tech):** a pull request proposes your branch for the shared version. The CI workflow reruns the same
  checks automatically, so quality is verified by a machine before any human merges.
- **Together:** compare the three PRs: eval score, the cases each of you added, the hook message. No merge today. Who
  merges and what gets deployed is the IT team's call.

## Part 5. Debrief (5 min)
What the IT team does next (hardening, deployment). What you keep: a plugin anyone can install, a prompt with its proof,
and a method. What you did for the judge, Claude Code can do for your skills: `claude plugin eval`.

---

## After the hackathon: make it yours for another sector
What you built is modular. To cover another sector, swap a few pieces and keep the rest.

| Piece | Change it? | How |
|---|---|---|
| Thesis | **Yes** | Run `/p2p:thesis` and set Team to your sector (8 healthcare teams are in the data) |
| Golden cases | **Yes** | About 10 edge cases in a new folder (`evals/cases_<sector>/`), against a fixed copy of your thesis (`evals/thesis_<sector>.md`). Run `python evals/run.py --thesis evals/thesis_<sector>.md --cases evals/cases_<sector>`. The guardrail of Part 3 protects this folder too |
| Data | **Separate project** | A step *before* Step 0: a pipeline that gathers company data (e.g. Capital IQ, Inven, web search) into one database, refreshed as needed. The only requirement: deliver it in the format the tool reads, or adjust the code to read from the database. Today that is three files (figures, facts, market data for the target price); merging them is an architecture choice for that project. |
| Judge prompt | Usually no | It says *how* to decide, not *which sector*. Rerun the evals to confirm |
| Code, dashboard, plugin, hook | **No** | Sector-agnostic by design |

**Recipe:** new thesis → new golden cases → run the evals until ≥ 80% → use the plugin as-is.
