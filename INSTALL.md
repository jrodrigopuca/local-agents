# How to use `install.py`

Installer to copy an agent (with its skills) or individual skills into a tool's
**global** configuration (Claude Code, opencode, Kiro CLI, Codex, Antigravity
CLI, or the shared `~/.agents` directory).

Automates "Pattern B" from [INTEGRATION.md](INTEGRATION.md): instead of the tool's
config REFERENCING the catalog, it COPIES the agent + skills into the tool's own
directories so they travel with the machine.

> Requirements: Python 3.9+ (stdlib only, zero external dependencies). The
> examples run the script directly (`./install.py`); on Windows, PowerShell
> and cmd need Python in front: `py -3 install.py --all --tool claude`, or
> `python install.py …`. Every host installs to the same folders under your
> user profile (`%USERPROFILE%\.claude`, `%USERPROFILE%\.codex`, …).

---

## Shortcut: Install the ENTIRE suite

Because the catalog is a suite where agents reference each other (handoffs,
cross-agent skills, orchestration), the most common workflow is to install
**everything together** — ensuring all interactions resolve cleanly:

```bash
./install.py --all --tool claude            # preview with --dry-run first
```

Installs all 15 agents (each with its inheritance inlined) + all 51 skills, each
skill installed exactly once. This is the recommended way to equip a tool with
the complete team.

---

## The three-step workflow (always the same)

**The golden rule: `--list` → `--dry-run` → install.** Never install blindly:
inspect what is available, preview the changes, and only then write to disk.

### Step 1 — Inspect what is available

```bash
cd ~/Developer/local-agents
./install.py --list
```

It shows each agent with the skills of its own and how many get installed
with it (what it inherits and links to), and then the tools:

```
Agents (15)
  architect        3 skills of its own, 7 installed with it
                   lh-design-review, lh-mentoring, lh-tradeoffs
  ...

Tools
  claude        available       agents and skills
  kiro          not detected    agents and skills
```

`available` means the tool's configuration directory was found. `not detected`
means it was not: you can still install into it, and the menu asks first.

### Step 2 — Preview with `--dry-run`

`--dry-run` says what the run would do and writes nothing. It opens and closes
by saying so:

```bash
./install.py --agent architect --tool claude --dry-run
```

```
Dry run: nothing is written.

Installing agent architect into claude (~/.claude)

  skills   would install 7
  agents   would install 1

Done (dry run): would install 8 files in claude.
Dry run: nothing was written. Run again without --dry-run to apply.
```

The counts are what the real run will report: for each file the dry run
works out whether it would be installed, updated or left as it is. Add
`--verbose` to see every file by name.

### Step 3 — Install for real (remove `--dry-run`)

```bash
./install.py --agent architect --tool claude
```

The agent is placed in `~/.claude/agents/architect.md` (with the frontmatter
`name`/`description` that Claude requires, generated automatically) and its skills
in `~/.claude/skills/`. Claude discovers them automatically via their `description`.

### What a run tells you

Installing, refreshing and uninstalling all report the same way: one row per
tool (or, for a single tool, one per kind of file), then what the run chose
not to touch, then one closing line.

```
Updating 2 tools from catalog a319a78

  claude        3 updated, 62 unchanged, 1 kept
  kiro          3 updated, 63 unchanged

Kept 1 file as it is:
  claude   skill lh-pairing   edited by hand   ~/.claude/skills/lh-pairing
It still has its old content. To replace it with the catalog's version:
  ./install.py --all --tool claude --on-conflict overwrite

Done: 6 files updated in 2 tools, 1 kept.
```

| Word | Meaning |
|---|---|
| `installed` | Was not there; now it is |
| `updated` | Was there and differed from the catalog |
| `unchanged` | Was there and already matched |
| `kept` | The run chose not to touch it, always with the reason: `edited by hand`, `not from this catalog`, `a link to another tool's copy` |
| `removed` | Deleted: an uninstall, or an old copy of a skill the catalog renamed |

A file that was kept is named again after the rows, with its path and the
command that replaces it, so it cannot be missed in a long run. When a refresh
finds nothing to bring, it says so in one line: `No installed file differs
from catalog a319a78. Nothing to update.`

`--verbose` prints one line per file under each tool.

---

## Interactive mode (guided menus)

If you don't want to remember flags, run the script with none:

```bash
./install.py
```

It asks three things — what to install (the whole catalog, one agent, one or
more skills), into which tool, and which one — and then installs and reports
like any other run, plus the command that takes it back:

```
Into which tool?
  1. claude        up to date
  2. opencode      nothing installed
  3. kiro          not detected
Choose (number, or q to quit):
```

- The tool list shows the state of each tool, the same row `--status` prints.
- `q` or Enter at any question leaves, and says `Cancelled: nothing was
  changed.` An answer that is not on the list is said and asked again; a list
  of skills with one wrong number is rejected whole, never installed in part.
- If something is already there and is not as the installer left it, it asks.
  Enter keeps it — the safe answer is the default, and it is shown as such:

  ```
  skill lh-mockups was edited by hand since it was installed.
    [k] keep your version (default)   [r] replace with the catalog's
  ```

  For something that is not from this catalog and has one of our names there
  is a third answer, `[n] install ours under another name`.
- With no one at the keyboard (a script, CI) the menu cannot be answered: it
  stops with an error and names `--list`.

---

## Non-standard paths (multi-account, containers, CI)

Two of the six tools publish an environment variable to override their config
directory, and the installer honors them:

| Tool | Variable | Default |
|---|---|---|
| Claude Code | `CLAUDE_CONFIG_DIR` | `~/.claude` |
| Codex | `CODEX_HOME` | `~/.codex` |

```bash
CLAUDE_CONFIG_DIR=~/.claude-work ./install.py --all --tool claude
```

Useful for the common multi-account scenario (personal and work) as well as
containers or CI where `HOME` differs. `--status` honors the same variables, so
it reports the directory currently in use.

The other four do **not** have overrides, by design: opencode documents a literal
`~/.config/opencode` and **does not read `XDG_CONFIG_HOME`** (do not "fix" it to
read it, that breaks); Kiro and Antigravity publish no variable; and `~/.agents`
is a convention of this catalog.

---

## Installing into a project (sharing with your team)

By default, files go to your global configuration (`~/`). With `--project`, files
go **inside the repository**, so configuration travels with the code: your teammate
clones and already has it, and CI can use it too.

```bash
./install.py --all --tool claude --project ~/code/my-repo
./install.py --all --tool claude --project          # no path = current directory
```

Where each tool lands:

| Tool | Global | Project |
|---|---|---|
| Claude Code | `~/.claude/` | `.claude/agents/` and `.claude/skills/` |
| opencode | `~/.config/opencode/` | `.opencode/agents/` and `.opencode/skills/` |
| Kiro CLI | `~/.kiro/` | `.kiro/agents/` and `.kiro/skills/` |
| Codex | `~/.codex/` | `.codex/agents/` and `.codex/skills/` |
| Antigravity CLI | `~/.gemini/config/` | `.agents/agents/` and `.agents/skills/` |

`shared` is the special case: it has no named agents, so per project its roster
goes to the root `AGENTS.md`, between markers — anything the team already has in
that file is preserved.

Codex used to be installed the same way. It now loads named agents from TOML
files, so the installer writes `agents/{name}.toml` and **retires the old
install** it finds: `.md` bodies that open with the roster header, and the
roster block (the file is deleted if nothing else was in it). Per project that
block is shared with `--tool shared`; if a shared install is present the block
stays, because it still serves it.

Antigravity keeps agents and skills globally under `~/.gemini/config/`, shared
with the IDE — not under `~/.gemini/antigravity-cli/skills/`, which its docs give
for the CLI but agy 1.3.3 does not read (measured). Per project both go under
`.agents/`. That is the same
directory `--tool shared --project` writes to, and the two write the same agent
paths in different formats: Antigravity needs frontmatter, the shared bodies
have none. Antigravity does not load a body without frontmatter as an agent:
`--agent NAME` silently gets the global agent of that name if you have one, or
its main agent if you don't — never the project's (measured on agy 1.3.3; a
valid project agent does win over a global one). So the
installer **refuses to mix them in one project**: use one of the two per repo.
Globally there is no clash — `~/.agents` and Antigravity's directories are
separate, and Antigravity does not read `~/.agents` at all.

**Project configuration overrides global** if they share a name, so a repo can
have its own version of an agent without affecting your personal setup.

Two guardrails: it refuses to install onto the catalog itself, and fails if the
target path does not exist.

> **Commit what is installed.** The point of `--project` is to travel with the
> repository; if you put it in `.gitignore`, you share nothing. `--status --project`
> tells you whether the committed copy is still up to date with the catalog.

---

## What happens to an agent during installation

The installed copy is not identical to the catalog file; three differences are deliberate:

1. **Inheritance is inlined.** The `CORE.md` of every agent in the frontmatter's
   `inherits:` list is embedded into the body, in that order, so the copied
   agent is self-contained (see below). Only that declaration counts; rewording
   the prose around it cannot change what gets inlined.
2. **Skill paths become NAMES.** In the catalog, the skills table links to
   `skills/{name}/SKILL.md` for navigation. When installed, the agent is a flat
   file and skills live in a sibling directory, so relative paths no longer resolve.
3. **Access tier translates to what the host can enforce.** Each agent declares
   `access: read` (consultative: reads, searches, delegates; never edits or runs)
   or `access: full`. In Claude Code that is a `tools:` allowlist; in opencode,
   `permission`; in Kiro, `tools` tags; in Antigravity, a `tools:` allowlist per
   tier (written for `full` too, because an agent without one gets almost no
   tools); in Codex, `sandbox_mode = "read-only"` for the read tier — which
   holds when the session's sandbox comes from config (`config.toml` or
   `-c sandbox_mode=...`), but not with the `--sandbox` flag, which overrides
   every agent file (measured on codex-cli 0.144.5); in `shared`, a lead note in the header because nothing
   there can enforce it. What no host can express by tool name remains a
   behavioral prompt promise guarded by the harness.

The second point arose from a real trace: an agent searched for its own skills,
failed to find them by path, and replied *"I could not read the catalog skills —
proceeding with my own judgment"*. **It operated without them.** The alternative
— rewriting paths to match each tool's layout — was discarded: there are multiple
targets with different layouts, and all hosts discover skills **by name** from
their descriptions. A name works across all hosts; a path works on only one.

The agent still finds them at runtime: it **searches** and locates them wherever
its host places them. The difference is that it now discovers them dynamically
rather than relying on a path that was only true on the machine where it was written.

Side effect: the "File" column in the skills table disappears in the installed copy,
because without a relative path it merely repeated the name under a misleading header.

## What happens to a skill during installation

Skills are also not copied verbatim. In the catalog, a skill links to others in
three ways, each handled differently during installation:

| In the catalog | Installed | Why |
|---|---|---|
| `../x/SKILL.md` (sibling, same agent) | unchanged | All tools install skills flat in a single directory, so it resolves |
| `../../../agent/skills/x/SKILL.md` (different agent) | `../x/SKILL.md` | Installed, EVERY skill is a sibling of all others across layouts |
| `../../AGENTS.md` or `../../../agent/AGENTS.md` | agent NAME | Agents live in a different directory with per-tool filenames; no relative path holds across hosts |

The link label always preserves the target name, so if a host displays the file
without resolving paths, the model can still search for the skill by name.
`validate.py` renders every skill as the installer would write it and fails if
any dead link remains (`installed-skills`).

---

## Which catalog version was installed from?

During installation, the script writes a `.local-agents.json` in the tool's
configuration directory with the catalog commit it copied from. `--status` reads
it and asks git for the rest:

```
Claude Code  (claude)
  /Users/you/.claude
    skills   51/51 from catalog
    agents   15/15 from catalog
    installed from 0035df7 — 2 commit(s) behind ed7c442
      skills changed: mockups, tradeoffs, verification
      agents changed: qa
```

No version numbers to maintain manually: **git history is the changelog**. The
manifest only stores where the copy originated; diffs are computed on the fly.

Degrades honestly rather than inventing a number:

| Situation | What it reports |
|---|---|
| Installed before stamping existed | `provenance: unknown` |
| Installed with uncommitted changes | `installed from abc1234 + uncommitted changes` |
| Commit no longer in history (rebase, different clone) | `that commit is not in this history; reinstall to resync` |
| Catalog is not a git checkout (zip archive) | `catalog is not a git checkout here` — installs anyway |

With `--project`, the manifest stays inside the repo. **Commit it**: it tells
the team which catalog commit they are currently using.

---

## What is installed and is it current?

`--list` tells you what you CAN install; `--status` tells you what IS
installed, and its first line answers the question you came with: is there
something to do?

```bash
./install.py --status
```

```
Everything installed is up to date.

  claude        up to date      15 agents, 51 skills
  opencode      up to date      15 agents, 51 skills
  kiro          not detected    (~/.kiro does not exist)
  codex         nothing installed
  ...

Catalog a319a78. Details: ./install.py --status --verbose
```

When something is behind, the headline counts the tools, each row names what
a refresh would bring, and the last lines are the command:

```
1 of 2 tools is out of date.

  claude        2 out of date   lh-icons, agent ux-ui
                1 edited by hand, kept as it is: lh-mockups
  opencode      up to date      15 agents, 51 skills

Next: ./install.py --refresh
      Updates only files this installer wrote. Files edited by hand
      and files not from this catalog stay as they are.
```

One row per tool, named by the key you pass to `--tool`:

| State | Meaning |
|---|---|
| `up to date` | Every installed file is what the catalog would write today |
| `N out of date` | N files differ from the catalog, or are missing from an install of the whole catalog. `--refresh` brings them |
| `nothing installed` | The tool is there; nothing from this catalog is |
| `not detected` | The tool's config directory does not exist |
| `edited by hand` (under a row) | A catalog file you changed. `--refresh` leaves it; it is not out of date |

**Out of date is decided by content, never by commits.** Every installed skill
and agent is rendered again through the installation pipeline and compared
with the file on disk. A catalog that moved eleven commits without changing a
file you have installed is not something to refresh for, and the status does
not say it is.

What a refresh alone would not fix comes after the rows as a warning, each
with the command that deals with it: an old copy of a skill the catalog
renamed, a skill of ours whose name a foreign skill holds, a skill another
directory serves out of date (below), a missing agent index.

`--status --verbose` gives every tool in full — what a normal run leaves out
because it is not a problem: the files that are not from this catalog, the
options that are off and how to turn them on, and the install record (which
catalog commit the install came from, and how many commits ago).

### One out-of-date copy is enough: `--refresh`

Some hosts read skills from several directories. opencode, measured on 1.18.11,
loads them from its own dir, from `~/.claude/skills`, from `~/.agents/skills`
and per project from `.agents/skills`, and keeps **one copy per name — not the
same one every time**: three identical runs took 32, 10 and 4 of 48 skills from
the project and the rest from global copies. Identical copies make that
harmless. An out-of-date one turns every load of that skill into a coin toss,
which is what the warning "also read from … is out of date there" reports.

Updating one tool does not fix it if another tool's copy is the one behind.
`--refresh` reinstalls the whole suite into **every tool that already holds a
catalog install** (it has a `.local-agents.json`), overwriting catalog files
only:

```bash
./install.py --refresh             # every global install
./install.py --refresh --project . # every install in this repo
```

The installer still writes one copy per tool and never relies on another
tool's: removing Claude Code must not take opencode's skills with it.

### New versions from GitHub: `update.py`

`--status` and `--refresh` compare against the clone on your disk; neither one
contacts the remote, so a clone nobody pulled reports "up to date" forever.
`update.py` is the part that talks to the remote. It is a separate script on
purpose: `install.py` stays offline and deterministic, and the network failures
stay out of it.

```bash
./update.py check      # fetch, then list the agents, skills and CORE files that changed
                       # since each install — writes nothing
./update.py update     # the same report, then git pull --ff-only and install.py --refresh
```

- **Which clone.** The one your installs were stamped from (`catalog_path` in
  `.local-agents.json`), wherever you run the script. If two installs come from
  two different clones it refuses, because only you can say which one is
  right.
- **It refuses rather than guesses.** It does not update a clone with
  uncommitted changes, or with commits that are not on the remote; it never
  merges, stashes or resets. On a developer's working clone, that is the
  usual answer, and nothing is touched.
- **Project installs** live in the team's repository and change on purpose.
  `update` names them and prints the `--refresh --project` command; it does not
  run it.
- **Exit codes:** `0` done or nothing to do · `1` error · `2` refused, nothing
  touched · `3` the remote could not be reached.

Without a clone at all, `bootstrap` makes one where you never have to look
(`$XDG_DATA_HOME/local-agents`, else `~/.local/share/local-agents`) and passes
every argument after it to `install.py`:

```bash
python3 update.py bootstrap --all --tool claude
```

It clones with `--filter=blob:none`: the whole history, which `--status` needs
to count commits, without downloading old file contents.

---

## Command Recipes

| Goal | Command |
|---|---|
| View everything available | `./install.py --list` |
| **Check installed status and staleness** | `./install.py --status` |
| **Bring every installed tool up to date** | `./install.py --refresh` |
| **See what changed on GitHub since you installed** | `./update.py check` |
| **Pull it and refresh every install** | `./update.py update` |
| **Install into a repository (for the team)** | `./install.py --all --tool claude --project ~/code/repo` |
| Preview (writes nothing) | add `--dry-run` to any command |
| **Install the full suite** | `./install.py --all --tool claude` |
| Install one agent + skills + inheritance | `./install.py --agent architect --tool claude` |
| One agent WITHOUT dependencies | `./install.py --agent architect --tool claude --no-deps` |
| Install a standalone skill | `./install.py --skill architect:tradeoffs --tool claude` |
| Multiple agents at once | `./install.py --agent qa --agent security --tool claude` |
| Guided menus | `./install.py` |
| **Claude Code: refuse file writes through the shell** | `./install.py --all --tool claude --shell-write-guard` |
| Take that guard out again | `./install.py --refresh --no-shell-write-guard` |
| **Claude Code: run each repo's declared check before an agent finishes** | `./install.py --all --tool claude --verify-hook` |
| Take that hook out again | `./install.py --refresh --no-verify-hook` |

The standalone skill format is `agent:skill` (run `--list` if you don't recall
the name). You can also provide just the skill name if it is unique.

---

## Optional: the shell-write guard (Claude Code)

The CORE rule "Approval follows the effect" says a file changes only through
the editing tool. Claude Code enforces that by itself only in its default mode:
`acceptEdits`, `auto` and `bypassPermissions` let a heredoc or `sed -i` write
the file, and `auto` and `bypass` even tell the model to edit that way.
`--shell-write-guard` closes the gap for the catalog's agents (B-083):

```bash
./install.py --all --tool claude --shell-write-guard
```

- It copies `scripts/shell_write_guard.py` to `~/.claude/hooks/local-agents/`
  and adds a `PreToolUse` hook on `Bash` to the frontmatter of every
  `access: full` agent. Your `settings.json`, your main session and other
  agents are not touched.
- A refused command reaches the agent as a refusal of the ROUTE, not of the
  change: use the editing tool; without one, say so and leave a diff.
- It refuses only bytes the agent decides: redirections to a file (anything
  under `/dev/` passes), heredocs into a file, `sed -i`/`perl -i`, `tee FILE`,
  inline scripts that open a file for writing, `cp`/`mv`/`touch`/`truncate`,
  `dd of=`, `git apply`, `patch`, `ed`. Project tools that write as a side
  effect (`npm install`, `npm run gen`, `prettier --write`, `node --test`),
  `rm`, `mkdir` and git state commands pass. A log redirected to `/tmp` is
  refused too: pipe it instead.
- If the guard itself breaks, it lets the command through and says so on
  stderr (fail-open): it guards a habit, and must not stop every shell
  command on a teammate's machine. It is a text match, not a sandbox.
- Off for one session: start Claude Code with `LOCAL_AGENTS_SHELL_GUARD=off`
  in its environment. Off for good: `./install.py --refresh --no-shell-write-guard`.
- `--refresh` keeps the choice (it is in the stamp); `--status --verbose`
  shows it under `options` for each Claude Code install.
- With `--project`, the hook points at `$CLAUDE_PROJECT_DIR/.claude/hooks/…`.
  Claude Code runs a project agent's frontmatter hooks only once the folder is
  trusted, and never under `claude -p`.
- Needs `python3` on the PATH. Where the command is missing the hook fails
  open, as above. Other hosts: not rendered yet. Kiro's agent JSON has
  `hooks.preToolUse`, but how a hook blocks there has not been verified.

---

## Optional: the verify hook (Claude Code)

The CORE asks an agent to verify before claiming done, and `lh-verification`
says how; but the one judging whether the work is verified is the model that
did it, and a model grading its own work leans to PASS. `--verify-hook` puts
that judgment outside the model (B-084): when an agent tries to finish, the
repo's own check runs, and if it is red the agent is sent back once with the
failure. It is the "machine-checkable stop rule" of loop engineering, in the
one place the catalog can put it without becoming host-specific.

```bash
./install.py --all --tool claude --verify-hook        # once, globally
printf 'npm test\n' > .local-agents/verify             # in each repo that wants it
```

- **Each repo declares its check** in `.local-agents/verify`: one line, the
  command (`npm test`, `pytest -q`, `go test ./...`, `swift test`,
  `make check`), `#` comments allowed. The hook looks for it from the
  session's working directory up to the repo root (the first directory with
  `.git`). Commit the file: the whole team gets the same check. An empty file
  (or comments only) opts the repo OUT, default included. The agents install
  globally and one command cannot fit every repo, so the catalog never infers
  one from `package.json` or a `Makefile`: a hook that guesses fails where
  nobody is watching.
- **`--verify-hook 'npm test'` records a default** for repos that declare
  nothing. Without one, a repo without the file is silent. A bare
  `--refresh --verify-hook` keeps the recorded default; a new CMD replaces it.
- It copies `scripts/verify_before_stop.py` to `~/.claude/hooks/local-agents/`
  and adds a `Stop` hook to the frontmatter of every `access: full` agent.
  Claude Code turns a subagent's `Stop` into `SubagentStop` (documented), so
  it fires when the agent finishes a delegation and when it runs as the main
  session. Your `settings.json`, your main session and other agents are not
  touched.
- Green is silent. Red blocks the stop ONCE, with the exit code and the last
  lines of the output as the reason the agent sees: fix it and run the check
  again, or finish by reporting the failure. The second attempt to finish
  goes through whatever the check says: one block per turn is a budget, not
  a loop (Claude Code also caps stop-hook continuations at 8).
- The agent can edit `.local-agents/verify` like any file. It is in git, so
  a check turned into `true` shows in the diff; review it as you would a
  deleted test.
- Fail-open: nothing declared and no default, a check that cannot start, a
  timeout (`LOCAL_AGENTS_VERIFY_TIMEOUT` seconds, default 300), bad input or
  a bug in the hook never block; the reason goes to stderr. A declared
  command that does not exist IS a red check (`command not found`, exit
  127): you see the mistake in the agent's reply, not a silent pass.
- Needs `python3` on the PATH, as the shell-write guard does; without it the
  hook fails open. You have Python if you ran `install.py`; teammates of a
  `--project` install may not, and for them the hook does nothing. The
  interpreter's name on Windows (`python`, `py`) is not handled yet (B-086).
- Off for one session: `LOCAL_AGENTS_VERIFY_HOOK=off` in Claude Code's
  environment. Off for good: `./install.py --refresh --no-verify-hook`.
- `--refresh` keeps the choice and the default (both in the stamp);
  `--status --verbose` shows it under `options` for each Claude Code install. With
  `--shell-write-guard` both hooks share the agent's one `hooks:` block.
- With `--project`, the hook points at `$CLAUDE_PROJECT_DIR/.claude/hooks/…`,
  and runs only once the folder is trusted, never under `claude -p`.
- Other hosts: not rendered yet. The script is host-neutral (JSON in, JSON
  out, the default on argv). Codex documents `Stop`/`SubagentStop` with the
  same input and output and a `SubagentStop` matcher on the agent type, so it
  could carry this script unchanged, but its hooks live in your
  `~/.codex/hooks.json` or `config.toml`, which the installer does not touch.
  opencode's `session.idle` cannot block a stop; Kiro and Antigravity have no
  known stop event. There the agents keep verifying in prose, as today.

---

## Optional: starting every session with an agent (`default_agent.py`)

A session started without an agent loads nothing from this catalog: the host's
own assistant answers, under the host's own instructions, and those differ per
host and per model (see [ESTADO-DEL-ARTE.es.md](ESTADO-DEL-ARTE.es.md),
section 3). `default_agent.py` makes an installed catalog agent the one a
session starts with, so its rules are there from the first turn.

`install.py` never does this. Which agent a session starts with is your
preference, not the catalog's, so it is a separate script you run yourself:

```bash
./default_agent.py --status                    # what each host starts with now
./default_agent.py --set generalist --dry-run  # show, change nothing
./default_agent.py --set generalist            # every supported host that is installed
./default_agent.py --set generalist --tool claude,kiro
./default_agent.py --restore                   # put back what was there before
```

```
$ ./default_agent.py --set generalist
  claude        now starts with `generalist` (was nothing)
                ~/.claude/settings.json
  opencode      now starts with `generalist` (was nothing)
                ~/.config/opencode/opencode.json
  kiro          already `generalist`

Undo: ./default_agent.py --restore
```

One row per tool, the settings file it touched under it. `--verbose` adds the
name of the setting and how to pick another agent for one session.

| Host | Setting it writes | Another agent for one session |
|---|---|---|
| Claude Code | `agent` in `~/.claude/settings.json` | `claude --agent NAME` |
| opencode | `default_agent` in `~/.config/opencode/opencode.json` | Tab, or `opencode --agent NAME` |
| Kiro CLI | `chat.defaultAgent` in `~/.kiro/settings/cli.json` | `kiro-cli chat --agent NAME` |

- It is the gentle way in: the default is only where a session STARTS, and
  choosing another agent still works.
- The agent has to be installed in that host first, and in opencode it has to
  be a primary agent: opencode falls back to its own `build` without a word
  otherwise. The script refuses both cases.
- A settings file that is not plain JSON (comments, a trailing comma) is
  refused, never rewritten: add the line by hand.
- **The way back.** The value that was there before is recorded beside the
  setting (`.local-agents-default-agent.json`) when the change is made.
  `--restore` puts it back only if the setting is still the one the script
  wrote; a value you changed afterwards is yours and is left alone.
- In Claude Code a main-thread agent REPLACES the default system prompt
  (documented); `CLAUDE.md` and project memory still load.

**Codex and Antigravity have no such setting** (read 2026-11-15, not
measured). The only way to reach a session without an agent there is the
host's global rules file — `~/.codex/AGENTS.md`, `~/.gemini/AGENTS.md` — and
nothing here writes it, because it is not the same kind of change:

- it loads in EVERY session and inside every agent, yours included, and
  cannot be skipped for one session;
- an agent from this catalog would then carry the same rules twice;
- the files are shared across tools: opencode reads `~/.claude/CLAUDE.md`
  when it has no rules file of its own, and `~/.gemini/GEMINI.md` is read by
  both Gemini CLI and Antigravity.

If you want it anyway, paste the rules you need from
[generalist/CORE.md](generalist/CORE.md) into that file yourself, between two
marker lines of your own, so you can find and remove them later.

---

## Dependencies and Inheritance (Important)

When you install an agent, the script **also installs what that agent needs to
function properly**, because copying breaks the catalog's reference tree:

- **Cross-agent skills**: if an agent references another agent's skills (e.g.
  security's `lh-remediation` uses qa's `lh-bug-reporting`), those skills are installed
  as well. Claude discovers them by `description`.
- **Inlined inheritance**: almost all agents inherit reasoning from `generalist`,
  and "peer" agents adopt the Peer Contract from `senior-dev`. Because installing
  the parent as a separate agent does NOT inject its reasoning into the child at
  runtime, the script **inlines** the parent's essence into the installed agent's
  prompt ("Inherited context" section). It uses the parent's **`CORE.md`** — a
  curated, condensed version of its always-on rules, rather than dumping the whole
  file. If a parent lacks `CORE.md`, it falls back to the full body. This keeps
  the copied agent self-contained and lightweight.

To install ONLY the agent and its own skills, without dependencies:

```bash
./install.py --agent architect --tool claude --no-deps
```

> With `--all`, this is already handled: all agents and skills are installed,
> so beyond inlined inheritance, handoffs and orchestration between agents also
> resolve cleanly.

---

## What it touches: ours, edited, foreign

A host's skills dir is shared with every other tool that installs skills —
`npx skills` writes there too, and 26 of our 48 skill names already exist in
public registries. So `install.py` never decides by name. Every catalog skill
carries `metadata.local-agents-id`, and the install record — the stamp,
`.local-agents.json` in the tool's directory — records the hash of every skill and agent file as it was written. With those,
each thing already at a destination is one of:

| Kind | What the output calls it | How it is told | What happens |
|---|---|---|---|
| **ours** | (counted as `installed`, `updated`, `unchanged`) | our id, at its own name, hash as recorded | updated, always |
| **edited** | `edited by hand` | our id (or recorded by the stamp), hash changed since we wrote it | kept, and named at the end of the run — unless you say `--on-conflict overwrite` |
| **foreign** | `not from this catalog` | no id of ours (an agent file the stamp never recorded) | kept, and named at the end of the run — unless you say `--on-conflict overwrite` |
| **link** | `a link to another tool's copy` | a symlink (`npx skills` links each host to its own copy) | always kept: never followed, never deleted |
| **retired** | `old copy` | our id under another name while the real one is installed at its own name (a renamed skill's old copy, a `-2` an older installer left), or an id the catalog no longer has | removed by `--refresh` and `--all` when it is intact (the hash the stamp recorded under that old name) — otherwise a host lists both and may load the old one; an edited one, or one the stamp has no record of, is kept and reported by `--status` with its `rm` command |
| **ours, under another name** | `installed as <name>` | our id under another name, and no copy at its own name (`--on-conflict rename` next to a foreign skill) | updated in place on the next run; never offered for deletion |

The left column is the name the code uses; the second is the one you read.
`--status --verbose` shows each kind per tool. `--refresh` updates what is ours and
nothing else, so it is always safe to run — and it keeps the shape of the
install: where the whole catalog was installed it brings new skills and
agents too; where one agent or one skill was, it refreshes exactly that (the
stamp records which, as `"suite"`).

Every path that installs writes the stamp, a catalog that is not a git
checkout included (it records no commit, but still records what it wrote).

**Installs from before B-058** have a stamp with a commit and no hashes. The
installer rebuilds them: it renders that commit of the catalog the way it was
installed and compares file by file, so a copy edited by hand since then is
recognized and left alone, and the rest is updated. If the commit is not in
this clone, it says so and falls back to the old rule (a skill with
`metadata.author: jrodrigopuca`, an agent with a catalog name, count as ours).
An install with no stamp at all keeps its skills updated by the same author
rule; its agents have no record, and `--status` says how to adopt them once.

### `--on-conflict`

It only matters for **edited** and **foreign** things; what is ours is always
updated and a link is always left alone.

| Value | Edited or foreign at the destination |
|---|---|
| `ask` (default) | Asks in a terminal; without one (a script, `local-hero`), leaves it and says so |
| `overwrite` | Replaces it — the explicit way to say "this one too" |
| `rename` | Installs ours next to a foreign one as `-2`, `-3`… (**rewrites `name:`** to match). Agents still load the foreign one by its name; rarely what you want |
| `skip` | Leaves it, silently |

Before B-058, `ask` without a terminal renamed **everything** that existed,
ours included: running the default command twice installed the whole catalog
twice. Copies like that show up in `--status` as old copies, with the `rm -r`
that removes them.

---

## Uninstalling: `--uninstall`

The way back takes what the installer put, and only that.

```bash
./install.py --uninstall --dry-run     # show what would go, change nothing
./install.py --uninstall               # every tool that holds a catalog install
./install.py --uninstall --tool kiro   # only that one
./install.py --uninstall --project .   # a project's install, not your home's
```

It decides what is "ours" the way every other path does (see above): by the
skill's id and by the hash the stamp recorded, never by name.

| In the host's directory | What happens |
|---|---|
| A catalog skill or agent, still as it was installed | Removed |
| The hook scripts the installer copied, still as copied | Removed |
| The roster block in `AGENTS.md` | Removed; everything outside the markers stays, and a file that held nothing else goes with it |
| The stamp, `.local-agents.json` | Removed |
| A catalog skill, agent or hook script you **edited** since | Kept, and named in the output |
| Anything foreign, even with one of our names | Not touched |
| A directory left empty (`skills/`, `agents/`, `hooks/`, a project's config dir) | Removed; your home's config dir never is |

- **What is kept is yours from then on.** The stamp goes either way, so the
  catalog no longer tracks an edited copy: delete it by hand if you do not want
  it. A leftover file costs less than a lost edit.
- **Kiro's backups stay.** Kiro writes a `.bak` next to every agent it
  upgrades; those files are Kiro's, and the output says how many remain.
- **The default agent is not this command's.** If a host is still set to start
  with an agent that was just removed, the output says so and names the
  command that puts the setting back: `./default_agent.py --restore`.
- **Measured, not promised:** for each of the six tools, and for a project,
  the tests install into a directory that already holds the user's own
  settings, skills and agents, uninstall, and compare the directory byte for
  byte with what it was (`tests/test_uninstall.py`). One limit: an `AGENTS.md`
  that did not end with exactly one newline comes back ending with one.

---

## Installation Destinations (Per Tool)

| Tool | Agents | Skills |
|---|---|---|
| Claude Code (`claude`) | `~/.claude/agents/{name}.md` | `~/.claude/skills/{name}/` |
| opencode (`opencode`) | `~/.config/opencode/agents/{name}.md` | `~/.config/opencode/skills/{name}/` |
| Kiro CLI (`kiro`) | `~/.kiro/agents/{name}.json` | `~/.kiro/skills/{name}/` |
| Codex (`codex`) | `~/.codex/agents/{name}.toml` | `~/.codex/skills/{name}/` |
| Antigravity CLI (`antigravity`) | `~/.gemini/config/agents/{name}.md` | `~/.gemini/config/skills/{name}/` |
| Shared (`shared`) | `~/.agents/agents/{name}.md` + roster in `~/.agents/AGENTS.md` | `~/.agents/skills/{name}/` (skills read by opencode + Codex; opencode does not read its agents) |

**Note on `shared`:** It is not a host, so nothing gives it named subagent
slots; the script addresses this in two parts: it copies the bodies into `agents/{name}.md`
and writes a **roster** (a one-line summary table per agent) into `AGENTS.md`, which
the host loads automatically. The model consults the roster and opens the relevant
agent body. Inlining all 15 bodies upfront would consume ~110 KB of context per session;
the roster is only ~3 KB.

The roster is written between `<!-- BEGIN:local-agents -->` / `<!-- END:local-agents -->`
markers: anything outside them is preserved verbatim, and reinstalling replaces the block
rather than duplicating it. The table indexes all agents present in `agents/`, not just
those from the current run.

**Note on `shared`:** `~/.agents/skills/` is read by both opencode and Codex — install once,
available to both.

---

## Useful Options

| Flag | Purpose |
|---|---|
| `--all` | Install the complete suite (15 agents + 51 skills) |
| `--no-deps` | Install only the agent's own skills, omitting inheritance and cross-agent skills |
| `--dry-run` | Say what the run would do, with the same counts, and write nothing |
| `--catalog PATH` | Use a different catalog (default: directory containing the script) |
| `--on-conflict {ask,overwrite,rename,skip}` | Collision policy |
| `--list` | List catalog contents and detected tools, then exit |
| `--project [PATH]` | Install into a repository instead of user home (no path = current dir) |
| `--status` | Check what is INSTALLED in each tool and whether it is up to date, then exit |
| `--verbose` | One line per file when installing, refreshing or uninstalling; with `--status`, every tool in full |
| `--refresh` | Reinstall the suite into every tool that already holds a catalog install |
| `--uninstall` | Remove what the installer put, and only that; edited and foreign files stay. With `--tool`, `--project`, `--dry-run` |

---

## Errors and exit codes

Every error has the same form, on stderr: what is wrong, what was found, and
a command that works.

```
error: --all needs a target tool.
  Tools: claude, opencode, kiro, codex, antigravity, shared
  Try: ./install.py --all --tool claude
```

A name that is close to a real one gets `Did you mean: …`. The `Try:` line is
a command you can run as it is: it carries the agents, skills and `--project`
you passed.

**A suggested command is one you can type.** Every `Try:` and `Next:` is built
from how you came in:

| You ran | A suggestion looks like |
|---|---|
| `./install.py …` inside the catalog | `./install.py --refresh` |
| `install.py` from another folder | `~/path/to/catalog/install.py --refresh` |
| `update.py …` | `./update.py update` |
| a launcher (`npx github:…/local-hero …`) | the launcher's own command, or its verb alone (`` `update` ``) from a launcher that does not say its name |

Whoever is in front says how it was typed in the environment variable
`LOCAL_AGENTS_FRONT`; `update.py` sets it for itself and for the `install.py`
it runs, and a launcher can set it first. Unset, the scripts suggest
themselves.

| Code | Prefix | Meaning |
|---|---|---|
| `0` | | Done |
| `1` | `error:` | It cannot be done: a mistyped flag, an unknown name, nothing installed to act on |
| `2` | `refused:` | It could be done and is not safe to. Always ends with `Nothing was changed.` |

These are the codes `update.py` and the `local-hero` launcher document (which
add `3`, the remote could not be reached), so a script around any of them
reads the same numbers. `default_agent.py` follows them too: `2` only when no
tool was changed, `1` when it refused in one tool and changed another.

---

## Adding a New Tool

The tool registry is data, not buried logic. Open `install.py`, locate the
`TOOLS = [...]` block, and append a `Tool(...)`:

```python
Tool("mytool", "My Tool",
     HOME / ".mytool",             # directory whose existence indicates installation
     HOME / ".mytool/skills",      # where skills land
     HOME / ".mytool/agents",      # where agents land (None if unsupported)
     "claude_md",                  # agent file format
     ".mytool"),                   # per-repo config dir, used by --project
```

This is sufficient **if the tool uses an existing format** (`claude_md`,
`opencode_md`, `kiro_json`, `antigravity_md`, `codex_toml`, `roster_md`). If it requires a NEW format,
add a corresponding branch in `render_agent()`.
