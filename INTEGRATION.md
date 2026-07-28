# Integrating Catalog Agents into Tool Configs

How to wire the agents in this catalog into any harness (opencode, Claude Code,
custom SDK agents) **without duplicating their prompts**. The rule that matters:

> The `AGENTS.md` file is the single source of truth. Configs REFERENCE it;
> they never copy it. A copied prompt is a fork that will silently rot.

## Pattern A — File reference (preferred)

Works when the harness lets the agent read files. The config prompt is a
one-liner that delegates to the catalog:

```json
"agent": {
  "architect": {
    "mode": "primary",
    "description": "Senior Architect mentor - helpful first, challenging when it matters",
    "prompt": "Read ~/Developer/local-agents/architect/AGENTS.md and fully adopt it: identity, judgment model, and escalation ladder. It inherits ~/Developer/local-agents/generalist/AGENTS.md — read that too. Load the skills it references when their triggers fire.",
    "tools": { "read": true, "write": true, "edit": true }
  },
  "generalist": {
    "mode": "primary",
    "description": "Multipurpose agent - reasoning loop, verification habits, decomposition",
    "prompt": "Read ~/Developer/local-agents/generalist/AGENTS.md and fully adopt it. Load the skills it references when their triggers fire.",
    "tools": { "read": true, "write": true, "edit": true }
  }
}
```

Requirements for this pattern:

1. **`read` tool must be enabled** — without it the agent can't load its own
   definition and you get a generic assistant with a nice description.
2. Paths must be absolute or `~`-based; the agent's cwd varies per session.
3. Agents that inherit another agent (architect → generalist) must be told to
   read BOTH files, parent first is not required — the child file states what it
   inherits.

## Pattern B — Inline paste (fallback)

For harnesses that can't read files at startup (or agents with no filesystem
access): paste the full content of `{agent}/AGENTS.md` into the config's prompt
field. Every AGENTS.md in this catalog is written to work standalone.

Cost of this pattern: the config forks the source. If you use it, add a comment
in the config with the source path and re-paste after editing the catalog.

## Checklist when adding a new agent to a config

- [ ] Config prompt references the file, doesn't copy it (Pattern A)
- [ ] `read` enabled in tools
- [ ] Inherited agents (if any) mentioned in the prompt
- [ ] Description in the config matches the row in [AGENTS.md](AGENTS.md)

## Skills loading note

Skills (`{agent}/skills/*/SKILL.md`) are NOT loaded upfront — that's by design
(progressive disclosure keeps the base context small). The AGENTS.md tells the
model when to load each one. No config wiring is needed for skills beyond `read`
permission.
