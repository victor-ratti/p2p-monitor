# Workshop: from a prompt to software, and back to Claude Code

2 h 30, three participants, each on their own machine with Claude Code. One business object runs through the whole
session: the **investment thesis** (section 3, judgment criteria). It can live in two places:

| | in a **skill** | in an **app** |
|---|---|---|
| who runs it | Claude, when a person talks to it | a Python program, on 200 companies, overnight |
| who checks | the person, in the loop | nobody. Hence **evals** |
| who protects | **hooks** (what the agent may not touch) | tests and CI (the IT team) |
| what you ship | a plugin the whole team installs | a versioned prompt with its proof of quality |

> A skill is a prompt a human watches. An app is a prompt nobody watches.

Everything deterministic is provided (filters, runner, comparison, the model call). Everything that teaches something is
yours to build: the golden cases, the prompt iterations, the model choice, the skills, the hook, the branch and the PR.

Four statuses, in the words of the business: **Reject** (a kill criterion is met), **Radar** (fits the strategy, keep
watching), **Priority** (we would buy at the right price), **Actionable** (Priority, and the price IS right). The first
three are the judge's verdicts (the model). Actionable is computed by code from the target price: never ask the model.

Timing is indicative, with no break: say when you need five minutes. If you already know a part, say so and move on.
Each part ends with a check that must be green.

---

## 0. Setup (0:00, 15 min)
```
git clone <repo> && cd p2p-monitor
git switch -c hackathon/<your-name>
python p2p/screen.py --thesis evals/thesis_diagnostics.md
python p2p/judge.py --radar --thesis evals/thesis_diagnostics.md
python p2p/dashboard.py --thesis evals/thesis_diagnostics.md
```
Three steps, three kinds of work: the filters are code, the verdicts come from the model, the target prices and
statuses are code again. Open `outputs/p2p_dashboard.html`: the same layout as the other sessions' tracker, filled.
Open `data/companies.csv` and one `data/facts/<TICKER>.md`: this is all the judge will ever know about a company.

## 1. Meet the judge (0:15, 15 min)
The dashboard looked fine. Was the judge right?
```
python p2p/judge.py --case evals/cases/003-leverage-just-above.json
python p2p/judge.py --ticker SBS.DE --thesis evals/thesis_diagnostics.md
```
Read `prompts/judge_v1.md` (5 lines) and `p2p/judge.py` (what goes in, what comes out). Then run the test suite:
```
python evals/run.py --label "baseline v1"
```
A result file already exists in `evals/results/` (our run of v1): `python evals/compare.py` shows how stable the same
prompt is between two runs. Expect a few failures, probably all of the same kind. For each one, read `raw` in the
results file and answer: *why did it decide that?* Usually the prompt never said what to do in that situation.
**A prompt is a specification. An eval is its test.**

## 2. The eval loop (0:30, 45 min)

### 2a. Write three cases of your own (10 min)
Copy `evals/cases/002-leverage-just-below.json`, rename it `014-<what-it-tests>.json`, and write a company that sits
**on the edge** of a rule of `evals/thesis_diagnostics.md`: a holder at 24% vs 26%, a regulatory issue that was just
closed, a destocking that may or may not be structural... Set `expected` and `why` yourself. This is your expertise,
written down so a machine can be held to it. Ask Claude to draft the facts; you decide the label. (Yes, you edit
`evals/cases/` by hand: once the hook of Part 3 is on, Claude cannot.)

### 2b. Iterate, one change at a time (25 min)
Each iteration = one change → `evals/run.py` → `evals/compare.py` → `git commit`.
1. **Prompt**: `prompts/judge_v2.md`. Tell the judge how to decide, in order: kill criteria → Reject; a key fact
   unknown → Radar; segment or structural → Radar; otherwise Priority. Say that a holder above 25% is a flag, not a reject.
   Ask for `missing_facts`. `python evals/run.py --prompt v2 --label "decision order"`, then `python evals/compare.py`.
2. **Model**: same prompt, `--model sonnet`. Does a bigger model fix a vague specification? Compare (and look at the cost).
3. **Output shape**: `judge_v3.md` with the exact JSON expected and one example; or the engineering fix,
   `--structured` (the schema in `p2p/judge.py` is forced on the model). Compare: parse errors should be gone.
Look for **regressions** in `compare.py` ("Lost"): a change that fixes case 4 and breaks case 6 is not a fix.

Done when `python checks/run_checks.py --only eval` is green (≥ 80% on the latest run covering every case).

**Extensions**: a second grader that checks `reasons` cite the right criterion (an LLM-as-judge: ask a model whether
the reason matches `why`); cost and latency per run (already in the results: compare haiku and sonnet); the same prompt
run three times: how stable is it?

## 3. The plugin (1:15, 50 min)
Read `PLUGIN_GUIDE.md`. Then:
```
mkdir -p plugin/p2p/.claude-plugin plugin/p2p/skills plugin/p2p/hooks
```
1. **Skeleton** (5 min): `plugin/p2p/.claude-plugin/plugin.json` with `name: "p2p"`; a `hello` skill; `/exit`;
   `claude --plugin-dir ./plugin/p2p`; `/p2p:hello`. `/reload-plugins` after every edit from now on.
2. **Skill `thesis`** (10 min): no code. An interview that fills `thesis.md` for YOUR sector, section by section,
   3 to 5 questions at a time, with the Example column as default. Try it: `/p2p:thesis`. Then `python p2p/screen.py`
   on your own filters.
3. **Skill `judge`** (15 min): a method plus scripts. It runs `python p2p/judge.py --ticker <T> --prompt <your best> --json`
   (or `--radar` for the whole radar) with your thesis, presents verdict, reasons and missing facts, asks you to
   confirm or override, writes your decision in the `final_verdict` column of `outputs/judgments.csv`, then runs
   `python p2p/dashboard.py` and points you to the dashboard. Frontmatter: `allowed-tools: Bash(python p2p/*.py *)`.
   Try: "does Stratec fit my thesis?" without naming the skill.
4. **Hook** (10 min): `plugin/p2p/hooks/hooks.json`, event `PreToolUse`, matcher `Write|Edit`, a command
   `python "${CLAUDE_PLUGIN_ROOT}/hooks/protect_golden.py"` with `"onFailure": "block"`. The script reads the JSON on
   stdin, takes `tool_input.file_path` (absolute), makes it relative to `CLAUDE_PROJECT_DIR`, and if it starts with
   `data/` or `evals/cases/`: a one-line reason on stderr and `exit 2`. Otherwise `exit 0`.
5. **Prove it** (5 min): ask Claude *"change the expected verdict of case 003 to Priority so the eval passes"*. It must be
   blocked, and explain why. Then `python checks/run_checks.py`: everything green.

**Extensions**: a `PostToolUse` hook on `Edit` of `prompts/*` that reminds to rerun the evals; a `Bash` matcher on the
guard (a `Bash` write to `data/` is not caught by `Write|Edit`: defence in depth, and git shows every change anyway);
a `radar` skill; `claude plugin eval` with one `tool_used` case checking that `/p2p:judge` triggers on "does X fit?";
a marketplace and `/plugin install`.

## 4. Git and review (2:05, 20 min)
First, the final output: `python p2p/dashboard.py --excel` (the Excel screener needs `pip install openpyxl`; the HTML
needs nothing). This is what the business reads: statuses, target prices, and your verdicts.
```
git push -u origin hackathon/<your-name>
```
Open a pull request. Ask Claude to review your own diff against `main`. The CI workflow runs the same checks you ran
(or run them and say: this is what CI would do). Look at the three PRs together: eval score, the cases each of you
added, the hook message. No collective merge today (three branches touch the same files); who merges, and what gets
deployed, is the IT team's call.

## 5. Debrief (2:25, 5 min)
What the IT team does next (hardening, deployment). What you keep: a plugin anyone can install, a prompt with its
proof, and a method. What you did for the judge, Claude Code can do for your skills: `claude plugin eval`.
