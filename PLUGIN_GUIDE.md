# Plugin guide: how a Claude Code plugin is built

Keep this open during the hackathon. It is short on purpose: the whole day is about these few ideas.

## What a plugin is
A **plugin** is a folder you can install in Claude Code to give it new abilities. A **skill** is one ability: a
folder with a `SKILL.md` file that tells Claude *when* to use it and *what to do*. A skill can also run **scripts**
(here, small Python programs) for everything that must be calculated exactly. In this hackathon:

> **Skills judge, talk and orchestrate. Scripts calculate. The plugin bundles both so anyone can install it.**

## The layout you will build
```
p2p-plugin/
  .claude-plugin/
    plugin.json                 the plugin's identity (name, description, version)
  skills/
    thesis/SKILL.md             one folder per skill; the folder name is the skill name
    radar/SKILL.md
    screener/SKILL.md
    thesis-judge/SKILL.md
  scripts/
    p2p_common.py  radar.py  valuation.py  screener.py  priority.py
```
Only `plugin.json` goes inside `.claude-plugin/`. A skill placed anywhere else is silently ignored.

### `plugin.json`
```json
{
  "name": "p2p",
  "description": "Buyout monitor for listed companies: thesis, radar, screener, thesis-judge.",
  "version": "0.1.0",
  "author": { "name": "Your name" }
}
```
`name` is the only required key: lowercase words joined by hyphens. It becomes the prefix of every skill:
the skill `radar` of the plugin `p2p` is called with `/p2p:radar`.

### A skill: `skills/radar/SKILL.md`
```markdown
---
name: radar
description: Build the radar, the list of listed companies that pass the filters of the thesis. Use when the user asks who passes the filters, for the landscape or the long list.
---

# Radar
1. Run `uv run "${CLAUDE_PLUGIN_ROOT}/scripts/radar.py"` from the user's project folder.
2. Read `outputs/radar/radar_summary.md` and tell the user how many companies pass and why the others do not.
```
- **`description` is the most important line.** Claude reads every skill's description to decide when to use it
  (and you can always call it yourself with `/p2p:radar`). Put the use case first: "Use when the user asks...".
- The body is a **recipe** addressed to Claude: numbered steps, rules ("never compute a number in the chat"), what to
  show the user. Short and concrete beats long and clever.
- Optional frontmatter: `argument-hint` (shown while typing), `allowed-tools: Bash(uv run ${CLAUDE_PLUGIN_ROOT}/scripts/*)`
  to skip permission prompts for your own scripts, `disable-model-invocation: true` if only the user may start it.

## Skills that run scripts
- Write `${CLAUDE_PLUGIN_ROOT}` **literally in the SKILL.md text**. Claude Code replaces it with the plugin's real
  path before Claude reads it. (It is *not* an environment variable inside the terminal: do not use it in a script.)
- Scripts read and write the **user's files in the current folder** (`03_inputs/`, `outputs/`), never files inside
  the plugin, except their own code. Give each script a `--workspace DIR` option, default = current folder.
- Why scripts and not Claude's own arithmetic: a script gives the same answer every time, can be checked against a known
  example, and leaves a file the user can open. That is what `checks/run_checks.py` verifies.
- Scripts declare their dependencies in a header, so `uv run` installs them on the fly (no setup):
  ```python
  # /// script
  # requires-python = ">=3.10"
  # dependencies = ["pandas", "openpyxl"]
  # ///
  ```
  No `uv`? `python -X utf8 script.py` works if `pandas` and `openpyxl` are installed (`pip install pandas openpyxl`).

## The development loop
1. Start Claude Code **with your plugin loaded**, from the repo root:
   ```
   claude --plugin-dir ./p2p-plugin
   ```
   (Part 0 creates the folder first; then quit with `/exit` and restart this way.)
2. After every edit to a skill or script, in the same session: `/reload-plugins`.
3. Check it is loaded: type `/` and look for `p2p:` skills, or open `/plugin` and look at the **Installed** and
   **Errors** tabs. An error there tells you exactly what is wrong (bad JSON, missing description, wrong folder).
4. Try the skill for real: `/p2p:radar`, or just ask in plain words ("who passes my filters?").
5. Run the acceptance checks: `python checks/run_checks.py` (all) or `--only radar`. Green means the part is done.
6. If your Claude Code has the `claude plugin validate ./p2p-plugin` command, run it too: it catches layout mistakes.

First time a skill runs a script, ask Claude to print the folder it runs in (`pwd` / `cd`). It must be the folder
that contains `03_inputs/`. If not, pass `--workspace` explicitly.

## Packaging and installing (Part 5)
A **marketplace** is a catalog of plugins: one JSON file listing where each plugin lives. Create
`.claude-plugin/marketplace.json` at the repo root:
```json
{
  "name": "archimed-p2p",
  "owner": { "name": "Your team" },
  "description": "P2P hackathon plugins",
  "plugins": [
    { "name": "p2p", "source": "./p2p-plugin", "description": "Buyout monitor: thesis, radar, screener, judge" }
  ]
}
```
- `source` is a path relative to the marketplace root (the folder that contains `.claude-plugin/`), without `..`.
- The `name` of a plugin entry must equal the `name` in its `plugin.json`.

Install like a user (in Claude Code, from any folder):
```
/plugin marketplace add ./path/to/the/repo        a local folder
/plugin marketplace add owner/repo                a GitHub repository (needs git access on your machine)
/plugin install p2p@archimed-p2p
```
Then `/reload-plugins`. To share the best plugin at the end of the day: copy its folder and `marketplace.json` into one
shared repository or folder and let everyone run the two commands above.

Updating: if `plugin.json` has a `version`, users only get changes when you change that string. Bump it when you ship.
A local-folder marketplace loads the files in place, so it does not test the *installed copy*: after installing from a
git repository, run the checks against the installed plugin too if you can.

## Mac and Windows
- Claude Code on Windows runs shell commands through Git Bash (when Git for Windows is installed) or PowerShell.
  Your scripts must therefore be plain Python, with `pathlib` for paths and `-X utf8` for text, never `.sh` or `.ps1`.
- Open the dashboard with `start outputs\p2p_dashboard.html` (Windows), `open outputs/p2p_dashboard.html` (Mac).
- `${CLAUDE_PLUGIN_ROOT}` is substituted with forward slashes on Windows; Python accepts them.

## Common problems
| Symptom | Likely cause | Fix |
|---|---|---|
| `/p2p:...` skills do not show up | Claude Code not started with `--plugin-dir`, or skills not in `skills/<name>/SKILL.md` | restart with the flag; check `/plugin` → Errors |
| Skill exists but Claude never picks it | weak `description` | start with "Use when the user asks...", add the words a user would say |
| Script: "file not found" after install | path built from `..` or the repo root | read user files from the current folder; keep plugin files inside the plugin |
| `uv` not found | not installed | `python -X utf8 ...` after `pip install pandas openpyxl`, or install uv |
| Garbled accents on Windows | console encoding | run Python with `-X utf8`; write files as UTF-8 |
| Check says a name was found in the plugin | a company, ticker or team name in code or a comment | move it into `03_inputs/` (the sector is a setting) |
| Changes not visible | forgot to reload | `/reload-plugins`; if the plugin has a `version` and it was installed, bump it |
