# Plugin guide: how a Claude Code plugin is built

Keep this open during Part 3 of `WORKSHOP.md`. It is short on purpose: the whole part is about these few ideas.

## What a plugin is
A **plugin** is a folder you can install in Claude Code to give it new abilities. It bundles:
- **skills**: one ability each, a `SKILL.md` file that tells Claude *when* to use it and *what to do*. A skill can run
  the repo's **scripts** (`p2p/*.py`) for everything that must be calculated or judged the tested way;
- **hooks**: guardrails. A script Claude Code runs automatically on an event (here: before every file edit), which can
  block the action.

> **Skills talk and orchestrate. Scripts calculate (and call the tested judge). Hooks protect. The plugin bundles them
> so anyone can install it.**

## The layout you will build
```
plugin/p2p/
  .claude-plugin/
    plugin.json                 the plugin's identity (name, description, version)
  skills/
    hello/SKILL.md              one folder per skill; the folder name is the skill name
    thesis/SKILL.md
    judge/SKILL.md
  hooks/
    hooks.json                  which event runs which command
    protect_golden.py           the guardrail script
```
Only `plugin.json` goes inside `.claude-plugin/`. A skill or hook placed anywhere else is silently ignored.
The scripts stay where they are, in `p2p/` at the repo root: the plugin calls them, it does not copy them.

### `plugin.json`
```json
{
  "name": "p2p",
  "description": "Buyout monitor for listed companies: thesis interview and thesis judge.",
  "version": "0.1.0",
  "author": { "name": "Your name" }
}
```
`name` is the only required key: lowercase words joined by hyphens. It becomes the prefix of every skill:
the skill `judge` of the plugin `p2p` is called with `/p2p:judge`.

### A skill: `skills/hello/SKILL.md`
```markdown
---
name: hello
description: Say hello and list the files of the current project. Use when the user says hello to the p2p plugin.
---

# Hello
1. Greet the user in one line.
2. List the top-level files of the current folder.
```
- **`description` is the most important line.** Claude reads every skill's description to decide when to use it
  (and you can always call it yourself with `/p2p:hello`). Put the use case first: "Use when the user asks...", with the
  words a user would really say ("does X fit my thesis?").
- The body is a **recipe** addressed to Claude: numbered steps, rules ("never compute a number in the chat"), what to
  show the user. Short and concrete beats long and clever.
- Optional frontmatter: `argument-hint` (shown while typing), `allowed-tools` to skip permission prompts for your own
  scripts (Part 3.3 uses `allowed-tools: Bash(python p2p/*.py *)`), `disable-model-invocation: true` if only the user
  may start it.

## Skills that run scripts
- Skills run from the **project folder** (the repo root), so they call the scripts by their relative path:
  `python p2p/judge.py --ticker <T> --json`. Ask for `--json` when Claude has to read the result.
- Why scripts and not Claude's own reasoning in the chat: a script gives the same answer every time, uses the prompt you
  tested in Part 2, and leaves a file the user can open (`outputs/`).
- **Keep the plugin sector-agnostic.** No company, ticker or team name in a skill or a hook: they belong in `thesis.md`.
  A skill that needs defaults reads them from the file (the `thesis` skill offers the **Example** column of `thesis.md`).
  `python checks/run_checks.py --only names` fails if it finds one.
- Standard library only, as in the rest of the repo: no `uv`, no `pandas`.

## Hooks
`hooks/hooks.json` says which command runs on which event. The guard of Part 3.4:
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          { "type": "command", "command": "python \"${CLAUDE_PLUGIN_ROOT}/hooks/protect_golden.py\"", "onFailure": "block" }
        ]
      }
    ]
  }
}
```
- **`PreToolUse`** runs *before* the tool, so the write never happens. `matcher` is a regular expression on the tool
  name: `Write|Edit` covers both file tools.
- The script receives the tool call as JSON on **stdin**: `tool_name`, `tool_input.file_path` (absolute), `cwd`...
  `CLAUDE_PROJECT_DIR` (the repo root) is in its environment.
- **Exit code 2 = block**: what the script prints on **stderr** is sent back to Claude as the reason, so write one clear
  line ("data/ and evals/cases are frozen: a human edits golden cases by hand"). **Exit 0 = allow.**
- `"onFailure": "block"` also blocks when the script itself crashes or times out (any exit code other than 0 or 2),
  instead of letting the write through. It needs a recent Claude Code: update it if `/plugin` reports the key as unknown.
- `${CLAUDE_PLUGIN_ROOT}` is replaced by the plugin's real path, so the command works wherever the plugin is installed.
- Limits: a `Bash` command (`echo x > data/companies.csv`) is not a `Write` or `Edit`. Defence in depth: add a `Bash`
  matcher (extension), and git shows every change anyway.

## The development loop
1. Start Claude Code **with your plugin loaded**, from the repo root:
   ```
   claude --plugin-dir ./plugin/p2p
   ```
   (Create the folder first, then quit with `/exit` and restart this way.)
2. After every edit to a skill or a hook, in the same session: `/reload-plugins`.
3. Check it is loaded: type `/` and look for `p2p:` skills, or open `/plugin` and look at the **Installed** and
   **Errors** tabs. An error there tells you exactly what is wrong (bad JSON, missing description, wrong folder).
4. Try the skill for real: `/p2p:judge`, or just ask in plain words ("does Stratec fit my thesis?").
5. Run the acceptance checks: `python checks/run_checks.py` (all) or `--only structure`, `--only hook`, `--only names`.
   Green means the part is done. The `hook` check feeds your script a fake write to `evals/cases/` and `data/` (must be
   blocked, with a message) and to `prompts/` (must be allowed).
6. If `claude` is installed, the `structure` check also runs `claude plugin validate ./plugin/p2p`.

## Packaging and installing (extension)
A **marketplace** is a catalog of plugins: one JSON file listing where each plugin lives. Create
`.claude-plugin/marketplace.json` at the repo root:
```json
{
  "name": "p2p-workshop",
  "owner": { "name": "Your team" },
  "description": "P2P hackathon plugins",
  "plugins": [
    { "name": "p2p", "source": "./plugin/p2p", "description": "Buyout monitor: thesis interview and thesis judge" }
  ]
}
```
- `source` is a path relative to the marketplace root (the folder that contains `.claude-plugin/`), without `..`.
- The `name` of a plugin entry must equal the `name` in its `plugin.json`.

Install like a user (in Claude Code):
```
/plugin marketplace add ./path/to/the/repo        a local folder
/plugin marketplace add owner/repo                a GitHub repository (needs git access on your machine)
/plugin install p2p@p2p-workshop
```
Then `/reload-plugins`. Updating: if `plugin.json` has a `version`, users only get changes when you change that string.
Bump it when you ship.

## Mac and Windows
- Claude Code on Windows runs shell commands through Git Bash (when Git for Windows is installed) or PowerShell.
  Hooks and scripts must therefore be plain Python, with `pathlib` for paths, never `.sh` or `.ps1`.
- In the hook, compare paths with `pathlib` (`Path(file_path).resolve().relative_to(project_dir)`), then test the
  `as_posix()` form: on Windows the separators are backslashes.
- `python` vs `python3`: write the one installed on your machine in `hooks.json` (the `hook` check tells you).
- Open the dashboard with `start outputs\p2p_dashboard.html` (Windows), `open outputs/p2p_dashboard.html` (Mac).

## Common problems
| Symptom | Likely cause | Fix |
|---|---|---|
| `/p2p:...` skills do not show up | Claude Code not started with `--plugin-dir`, or skills not in `skills/<name>/SKILL.md` | restart with the flag; check `/plugin` → Errors |
| Skill exists but Claude never picks it | weak `description` | start with "Use when the user asks...", add the words a user would say |
| The hook never blocks | wrong event or matcher, or the path is compared before being made relative | `PreToolUse` + `Write\|Edit`; print the relative path on stderr while debugging |
| The hook blocks everything | the script crashes (exit 1) and `onFailure` is `block` | run it by hand: `echo '{"tool_input":{"file_path":"..."}}' \| python plugin/p2p/hooks/protect_golden.py` |
| Check says a name was found in the plugin | a company, ticker or team name in a skill, hook or comment | move it into `thesis.md` (the sector is a setting) |
| Changes not visible | forgot to reload | `/reload-plugins`; if the plugin has a `version` and it was installed, bump it |
