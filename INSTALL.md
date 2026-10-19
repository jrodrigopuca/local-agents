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

Installs all 15 agents (each with its inheritance inlined) + all 48 skills, each
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

Displays agents with their skills, and detected tools below. An
`[available, agents+skills]` label means the script found that tool's configuration
directory and is ready to receive files. `[not detected]` = the tool is not
installed (you can install anyway; it will prompt you).

### Step 2 — Preview with `--dry-run`

`--dry-run` shows EXACTLY what files would be written without modifying anything:

```bash
./install.py --agent architect --tool claude --dry-run
```

Example output:

```
  Installing agent 'architect' → Claude Code
    skill  → /Users/you/.claude/skills/design-review
    skill  → /Users/you/.claude/skills/mentoring
    skill  → /Users/you/.claude/skills/tradeoffs
    agent  → /Users/you/.claude/agents/architect.md
```

### Step 3 — Install for real (remove `--dry-run`)

```bash
./install.py --agent architect --tool claude
```

The agent is placed in `~/.claude/agents/architect.md` (with the frontmatter
`name`/`description` that Claude requires, generated automatically) and its skills
in `~/.claude/skills/`. Claude discovers them automatically via their `description`.

---

## Interactive mode (guided menus)

If you don't want to remember flags, run the script directly:

```bash
./install.py
```

It guides you through interactive menus: whole suite / single agent / standalone
skill? → which one? → which tool? → and if something already exists, it prompts to
overwrite / rename / skip.

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
    skills   48/48 from catalog
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

`--list` tells you what you CAN install; `--status` tells you what IS installed:

```bash
./install.py --status
```

```
Claude Code  (claude)
  /Users/you/.claude
    skills   48/48 from catalog · 14 foreign (untouched)
    agents   15/15 from catalog

Codex  (codex)
  /Users/you/.codex
    skills   48/48 from catalog · 1 foreign (untouched)
    agents   15/15 from catalog
      roster: 15 rows in AGENTS.md
```

What each label means:

| Label | Meaning |
|---|---|
| `N/M from catalog` | How many catalog items are present |
| `stale` | Installed but **differs** from the catalog — needs reinstallation |
| `missing` | Present in catalog but missing from tool |
| `foreign (untouched)` | User-created, outside catalog. The installer never touches it |
| `roster: N rows` | shared: rows in `AGENTS.md`. Warns if count differs from bodies |
| `shadowing` | The host reads this skill from more than one dir and one copy is stale — names the dir and the command that refreshes it |

`stale` is computed by **content**, not timestamps: skills and agents are
re-rendered through the exact installation pipeline and compared with disk,
making "up to date" completely deterministic.

### One stale copy is enough: `--refresh`

Some hosts read skills from several directories. opencode, measured on 1.18.11,
loads them from its own dir, from `~/.claude/skills`, from `~/.agents/skills`
and per project from `.agents/skills`, and keeps **one copy per name — not the
same one every time**: three identical runs took 32, 10 and 4 of 48 skills from
the project and the rest from global copies. Identical copies make that
harmless. A stale one turns every load of that skill into a coin toss, which is
what `shadowing` reports.

Updating one tool does not fix it if another tool's copy is the stale one.
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
- `--refresh` keeps the choice (it is in the stamp); `--status` prints a
  `guard` line per Claude Code install.
- With `--project`, the hook points at `$CLAUDE_PROJECT_DIR/.claude/hooks/…`.
  Claude Code runs a project agent's frontmatter hooks only once the folder is
  trusted, and never under `claude -p`.
- Needs `python3` on the PATH. Where the command is missing the hook fails
  open, as above. Other hosts: not rendered yet. Kiro's agent JSON has
  `hooks.preToolUse`, but how a hook blocks there has not been verified.

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
carries `metadata.local-agents-id`, and the stamp (`.local-agents.json`)
records the hash of every skill and agent file as it was written. With those,
each thing already at a destination is one of:

| Kind | How it is told | What happens |
|---|---|---|
| **ours** | our id, at its own name, hash as recorded | updated, always |
| **edited** | our id (or recorded by the stamp), hash changed since we wrote it | left alone, with a warning — unless you say `--on-conflict overwrite` |
| **foreign** | no id of ours (an agent file the stamp never recorded) | left alone, with a warning — unless you say `--on-conflict overwrite` |
| **link** | a symlink (`npx skills` links each host to its own copy) | always left alone: never followed, never deleted |
| **retired** | our id under another name while the real one is installed at its own name (a renamed skill's old copy, a `-2` an older installer left), or an id the catalog no longer has | removed by `--refresh` and `--all` when it is intact (the hash the stamp recorded under that old name) — otherwise a host lists both and may load the old one; an edited one, or one the stamp has no record of, is kept and reported by `--status` with its `rm` command |
| **ours, under another name** | our id under another name, and no copy at its own name (`--on-conflict rename` next to a foreign skill) | updated in place on the next run; never offered for deletion |

`--status` shows each kind per host. `--refresh` updates what is ours and
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
twice. Copies like that show up in `--status` as retired.

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
| `--all` | Install the complete suite (15 agents + 48 skills) |
| `--no-deps` | Install only the agent's own skills, omitting inheritance and cross-agent skills |
| `--dry-run` | Show what would happen without writing files |
| `--catalog PATH` | Use a different catalog (default: directory containing the script) |
| `--on-conflict {ask,overwrite,rename,skip}` | Collision policy |
| `--list` | List catalog contents and detected tools, then exit |
| `--project [PATH]` | Install into a repository instead of user home (no path = current dir) |
| `--status` | Check what is INSTALLED in each tool and whether it is up to date, then exit |
| `--refresh` | Reinstall the suite into every tool that already holds a catalog install |

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
