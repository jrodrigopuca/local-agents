# Usage Guide: The Catalog in Each Tool

How to use the catalog's agents in Claude Code, opencode, Kiro CLI, Codex,
and Antigravity CLI — globally (available everywhere) or per project.
General principles (reference, never copy) are documented in
[INTEGRATION.md](INTEGRATION.md); these are concrete recipes per tool, verified
against official documentation (July 2026).

> **Paths in this guide.** Examples use `~/Developer/local-agents` (or
> `/Users/you/Developer/local-agents` where the tool requires an absolute path).
> Replace it with wherever you cloned the catalog. Absolute paths to a user home
> directory do not exist on a teammate's machine or in CI — see the final section.

## Summary: Tool Mechanisms

| Tool | Mechanism | Global | Per Project | References Files? |
|---|---|---|---|---|
| Claude Code | Subagents `.md` with frontmatter | `~/.claude/agents/` | `.claude/agents/` | Via "Read X" instruction in body |
| opencode | Agents `.md` with frontmatter, or JSON | `~/.config/opencode/agents/` | `.opencode/agents/` | Yes: `{file:...}` in JSON prompt |
| Kiro CLI | JSON agents | `~/.kiro/agents/` | `.kiro/agents/` | Yes, native: `"prompt": "file://..."` |
| Codex | Agents `.toml` + hierarchical AGENTS.md + skills | `~/.codex/agents/` and `~/.codex/skills/` | `.codex/agents/` and `AGENTS.md` at repo root | Via "Read X" instruction in `developer_instructions` |
| Antigravity CLI | Subagents `.md` with frontmatter + skills | `~/.gemini/config/agents/` and `~/.gemini/config/skills/` | `.agents/agents/` and `.agents/skills/` | Via "Read X" instruction in body |

Cross-cutting rule: **the agent requires read permission** to load its definition
and skills on demand. Without `read`, you have a generic assistant with a nice name.

---

## Claude Code

### Global (available in all projects)

Create `~/.claude/agents/architect.md`:

```markdown
---
name: architect
description: Senior Architect mentor - guidance on architecture, tradeoffs, design reviews, and learning paths. Helpful first, challenging when it matters.
---

Read /Users/you/Developer/local-agents/architect/AGENTS.md and fully adopt it:
identity, judgment model, and escalation ladder. It inherits
/Users/you/Developer/local-agents/generalist/AGENTS.md — read that too.
Load the skills it references when their triggers fire.
```

- The file body is the subagent's system prompt; minimum frontmatter is
  `name` + `description` (the description decides when Claude delegates —
  write it focusing on the trigger, not marketing).
- Optional: `tools:` to restrict tools and `model:` to pin a model.
  The installer writes `tools: Read, Grep, Glob, WebFetch, WebSearch, Agent, Skill`
  for catalog agents with `access: read`; `full` access agents inherit everything.
- Optional `hooks:` scopes hooks to one agent. They fire when it is spawned as
  a subagent and when it runs as the main session (`claude --agent`).
  `install.py --shell-write-guard` uses it to hook a `PreToolUse` guard on
  `Bash` into every `full` agent, and `--verify-hook` a `Stop` hook that runs
  the check each repo declares in `.local-agents/verify` before the agent
  finishes; see INSTALL.md, "the shell-write guard" and "the verify hook".
- Invoked explicitly ("use the architect agent") or Claude delegates automatically
  when the task matches the description.

### Per Project

The same file in `.claude/agents/architect.md` inside the repo. Project-level
overrides global if they share a name.

### Bonus: Catalog skills are directly compatible

The catalog's `SKILL.md` files follow the Agent Skills specification that Claude
Code reads natively. To expose a standalone skill without going through an agent:

```bash
ln -s ~/Developer/local-agents/generalist/skills/verification ~/.claude/skills/verification
```

Watch out for name collisions with existing skills; if they collide, rename the
symlink and ensure the frontmatter `name:` still matches the folder name.

---

## opencode

### Global

Create `~/.config/opencode/agents/architect.md` (filename = agent name):

```markdown
---
description: Senior Architect mentor - helpful first, challenging when it matters
mode: primary
---

Read /Users/you/Developer/local-agents/architect/AGENTS.md and fully adopt it:
identity, judgment model, and escalation ladder. It inherits
/Users/you/Developer/local-agents/generalist/AGENTS.md — read that too.
Load the skills it references when their triggers fire.
```

- `mode: primary` = selectable as primary agent (Tab);
  `mode: subagent` = delegable only.
- Frontmatter also supports `model`, `temperature`, and `permission` (e.g.
  `permission: { edit: deny }` for query-only agents). The installer emits
  `permission: { edit: deny, bash: deny }` for catalog agents with `access: read`.

### JSON alternative with `{file:}` — direct prompt without read instruction

In `opencode.json` the prompt can BE the file:

```json
"agent": {
  "architect": {
    "mode": "primary",
    "description": "Senior Architect mentor",
    "prompt": "{file:/Users/you/Developer/local-agents/architect/AGENTS.md}"
  }
}
```

Tradeoff: `{file:}` injects the content of `AGENTS.md` as system prompt (does not
depend on the model "reading properly"), but does NOT resolve inheritance — the
generalist is not included. For agents that inherit (architect, senior-dev, ux-ui),
the markdown variant with a "read both" instruction is more faithful. Paths in
`{file:}` resolve relative to the configuration file.

### Per Project

Same markdown in `.opencode/agents/architect.md` in the repo. Additionally, opencode
reads `AGENTS.md` at project root as general rules — there you can point to the
catalog so EVERY project agent knows the conventions.

---

## Kiro CLI

### Global

Create `~/.kiro/agents/architect.json` (filename = agent name):

```json
{
  "name": "architect",
  "description": "Senior Architect mentor - helpful first, challenging when it matters",
  "prompt": "file:///Users/you/Developer/local-agents/architect/AGENTS.md",
  "resources": [
    "file:///Users/you/Developer/local-agents/generalist/AGENTS.md"
  ],
  "tools": ["*"],
  "allowedTools": ["read"]
}
```

For consultative agents (`access: read` in the catalog: visionary and eng-manager),
the installer emits instead:

```json
  "tools": ["read", "grep", "glob", "web_fetch", "web_search", "subagent"],
  "allowedTools": ["read"]
```

Measured on kiro-cli 2.29.1: Kiro enforces `tools` (an agent with `["read"]`
could not write), `"*"` grants all 14 built-in tools, and two of them are not
what their names suggest. `code` edits files through its AST rewrite, so it is
not in the read list. `subagent` is, so a consultative agent can delegate — and
the agent it spawns can write, exactly like `Agent` in Claude Code.
`kiro-cli agent validate` accepts unknown tool tags without complaint, so it
cannot catch a misspelled one.

- `"prompt": "file://..."` is native Pattern A: absolute paths are used as-is,
  relative paths resolve from the config directory.
- `resources` preloads files as context — ideal for generalist inheritance.
  You can also preload skills with a glob
  (`"file:///Users/you/Developer/local-agents/architect/skills/**/*.md"`), but that
  breaks progressive disclosure: you pay the full context every time. Prefer
  preloading only the `AGENTS.md` files and letting skills load on demand with
  the `read` tool.

### Per Project

Same JSON in `.kiro/agents/architect.json` within the repo (scoped from that
directory down).

### Usage

```bash
kiro-cli agent list                    # verify it appears
kiro-cli chat --agent architect        # start with the agent
```

---

## Codex

Codex loads **named agents** from TOML files — one per agent, in
`~/.codex/agents/` or `.codex/agents/` — and keeps its instruction hierarchy in
`AGENTS.md` (concatenated from the root down to your directory; the closest takes
precedence). Measured on codex-cli 0.144.5. You ask for an agent by name in the
prompt ("have architect review this design").

> If you want the full suite, `./install.py --all --tool codex` does this
> automatically: one `~/.codex/agents/{name}.toml` per agent, with the composed
> body as `developer_instructions`. An older install (bodies as `.md` plus a
> roster block in `~/.codex/AGENTS.md`) is retired on the way; anything else in
> that file is kept. Below is the manual recipe for referencing the catalog
> instead of copying it.

### Global — a named agent

Create `~/.codex/agents/architect.toml`:

```toml
name = "architect"
description = "Senior Architect mentor - guidance on architecture, tradeoffs, design reviews, and learning paths."
developer_instructions = '''
Read /Users/you/Developer/local-agents/architect/AGENTS.md and fully adopt it:
identity, judgment model, and escalation ladder. It inherits
/Users/you/Developer/local-agents/generalist/AGENTS.md — read that too.
Load the skills it references when their triggers fire.
'''
```

For an `access: read` agent (`visionary`, `eng-manager`), add
`sandbox_mode = "read-only"`. For a `full` agent leave `sandbox_mode` out, so it
inherits the sandbox you chose for the session. Measured on codex-cli 0.144.5:

| How the session gets its sandbox | read-only agent | full agent |
|---|---|---|
| `config.toml` or `-c sandbox_mode="workspace-write"` | refuses to write | writes |
| `--sandbox workspace-write` flag | **writes** — the flag overrides every agent file | writes |
| nothing (`codex exec` defaults to read-only) | refuses | refuses (inherits read-only) |

So give the session write access through config, not through the `--sandbox`
flag. A project's own `.codex/config.toml` only applies once Codex trusts the
project.

### Global — generalist as the base for everything

In `~/.codex/AGENTS.md` (personal guidelines, applies everywhere):

```markdown
Adopt the reasoning model defined in
/Users/you/Developer/local-agents/generalist/AGENTS.md — operating loop, epistemic
rules, and reporting contract. Load the skills it references when their
triggers fire.
```

### Per Project — The role that repository needs

Either a TOML agent in `.codex/agents/`, or, in `AGENTS.md` at repository root:

```markdown
For this repository, additionally adopt
/Users/you/Developer/local-agents/senior-dev/AGENTS.md (work as a peer, not an
assistant).
```

Because files concatenate (global + project), inheritance builds itself: generalist
as global baseline, specific role per repository.

### Skills — directly compatible, just like in Claude Code

Codex deprecated custom prompts in favor of Agent Skills — the SAME `SKILL.md`
spec as the catalog. Symlink and done:

```bash
mkdir -p ~/.codex/skills
ln -s ~/Developer/local-agents/generalist/skills/verification ~/.codex/skills/verification
ln -s ~/Developer/local-agents/architect/skills/tradeoffs ~/.codex/skills/tradeoffs
```

Codex loads only name+description of each skill and fetches content when it matches
the task (native progressive disclosure). Invoked explicitly with `/skills` or
`$name`, or implicitly by description. Codex also scans `~/.agents/skills/` — a
location designed to be shared across tools; if another CLI adopts it tomorrow, a
single set of symlinks serves all.

---

## Antigravity CLI

Antigravity CLI (`agy`) replaced Gemini CLI for the free tier and Google One
accounts. It reads subagents as Markdown with YAML frontmatter and discovers
Agent Skills on demand. Globally both live under `~/.gemini/config/` (shared
with the Antigravity IDE): subagents in `agents/`, skills in `skills/`. Per
project, both live under `.agents/`. Sources: antigravity.google/docs/subagents
and /docs/skills — except the CLI skills path, where the docs say
`~/.gemini/antigravity-cli/skills/` and agy 1.3.3 does not read it (measured).

> If you want the full suite, `./install.py --all --tool antigravity` does this
> automatically: bodies to `~/.gemini/config/agents/`, skills to
> `~/.gemini/config/skills/`. No roster: Antigravity has named
> subagents, so every body is reachable on its own.

### Global (available in all projects)

Create `~/.gemini/config/agents/architect.md`:

```markdown
---
name: architect
description: Senior Architect mentor - guidance on architecture, tradeoffs, design reviews, and learning paths. Helpful first, challenging when it matters.
model: inherit
tools: [view_file, list_dir, find_by_name, grep_search, write_to_file, replace_file_content, multi_replace_file_content, run_command, read_url_content, search_web, invoke_subagent, define_subagent, manage_subagents, manage_task, send_message, schedule, ask_question]
---

Read /Users/you/Developer/local-agents/architect/AGENTS.md and fully adopt it:
identity, judgment model, and escalation ladder. It inherits
/Users/you/Developer/local-agents/generalist/AGENTS.md — read that too.
Load the skills it references when their triggers fire.
```

**Always declare `tools:`.** Omitted, Antigravity does not inherit the main
agent's tools: the subagent gets a minimal default with no grep, no file writes
and no shell (measured on agy 1.3.3). For an `access: read` agent (`visionary`,
`eng-manager`), use the read-only allowlist instead, so the host enforces what
the body promises:

```yaml
tools: [view_file, list_dir, find_by_name, grep_search, read_url_content, search_web, invoke_subagent]
```

Spell every name exactly: an unknown name aborts the agent at startup with
`tool "..." not found in registry`.

### Per Project

With `./install.py --all --tool antigravity --project <repo>`, agents land in
`.agents/agents/` and skills in `.agents/skills/` — the workspace paths
Antigravity reads.

### Skills

Catalog skills follow the `SKILL.md` specification (`name:` and `description:` in
frontmatter). Antigravity discovers them automatically and only loads the full
content when the task requires it.

---

## Global or Per Project? Decision Criteria

| Situation | Choose |
|---|---|
| Your default way of working, always (generalist) | Global |
| Roles you use everywhere (architect, senior-dev, ux-ui) | Global |
| A shared team repo: conventions traveling with code | Per Project (and commit the config) |
| Caution: per-project config referencing `~/Developer/local-agents` | Works ONLY on your machine — for teams, vendor the catalog into the repo or use Pattern B |

That last row is the pitfall to remember: absolute paths to your user home do not
exist on a teammate's machine or in CI.

## Smoke Test: Verifying the agent actually loaded

After configuring, do not assume — verify (rung 4, not rung 2). Open the agent and
ask something it only knows if it read the catalog:

> "What is your ladder of evidence and which rung does 'done' require?"

If it responds with the 4 rungs (Observed > Tested > Read > Recalled) and "minimum
rung 3", it loaded. If it gives a generic answer about testing, the prompt did not
reach it — check `read` permissions and paths.
