# local-agents

A catalog of **14 specialized AI agents and 45 skills** for software development,
installable into Claude Code, opencode, Kiro CLI, Codex, or any harness that can
read files.

Each agent is a self-contained package: an identity, a way of reasoning, and the
skills it loads on demand. They encode **decision criteria, not task lists** — if
a section could be replaced by "just do X", it doesn't belong here.

```bash
git clone https://github.com/jrodrigopuca/local-agents.git
cd local-agents
./install.py --list                        # see what's available
./install.py --all --tool claude --dry-run # preview
./install.py --all --tool claude           # install the whole suite
```

---

## The roster

| Agent | What it's for | Skills |
|-------|---------------|--------|
| [`generalist`](generalist/AGENTS.md) | Base reasoning loop: verification habits, decomposition, next-step decisions. Every other agent inherits this. | 3 |
| [`architect`](architect/AGENTS.md) | Architecture, expensive-to-reverse decisions, design review, mentoring. Helpful first, challenging when it counts. | 3 |
| [`senior-dev`](senior-dev/AGENTS.md) | Web/full-stack build work (JS/TS/React/Next) as a work peer. Defines the Peer Contract the team inherits. | 4 |
| [`ux-ui`](ux-ui/AGENTS.md) | Screen and flow design, mockups, design-to-dev handoff. Dev-fluent: speaks tokens, states, constraints. | 4 |
| [`qa`](qa/AGENTS.md) | Hunts unconsidered flows and edge cases. Writes test code, never fixes product code. | 3 |
| [`security`](security/AGENTS.md) | Defensive security: threat modeling, adversarial code audit, remediation. | 3 |
| [`devops`](devops/AGENTS.md) | CI/CD, infrastructure-as-code, observability, SLOs. Makes deploys boring and reversible. | 3 |
| [`data-ml`](data-ml/AGENTS.md) | Data pipelines, honest ML modeling, LLM integration (RAG, evals, cost/latency). | 3 |
| [`apple-dev`](apple-dev/AGENTS.md) | Swift/iOS/macOS as a sustained mentor: Socratic teaching, severity-tagged reviews, shipping. | 4 |
| [`product-manager`](product-manager/AGENTS.md) | Discovery, backlog, prioritization. Owns the why/what/for-whom. | 3 |
| [`visionary`](visionary/AGENTS.md) | Product vision and brutally honest critique. Focus as subtraction. | 3 |
| [`gamification`](gamification/AGENTS.md) | Flow analysis, engagement and habit mechanics — with an explicit ethics line. | 3 |
| [`stark`](stark/AGENTS.md) | Complex/stuck problems, 0→1 products, crises. First principles, build-to-think. | 3 |
| [`eng-manager`](eng-manager/AGENTS.md) | Orchestration: routes work across the roster, de-risks delivery. Knows every agent. | 3 |

Not sure which one you need? Start with `eng-manager` — routing is its job.

---

## How the agents connect

Three layers of relationship hold the suite together:

- **Inheritance** (21 edges) — structural. `generalist` carries the reasoning
  loop; `senior-dev` adds the Peer Contract on top for eight agents. The
  installer inlines the parent's `CORE.md` so every installed copy is
  self-contained.
- **Handoffs** (26 edges) — editorial. An agent names who takes over when a
  problem stops being its own.
- **Skill references** (90 cross-agent edges) — compositional. A skill points at
  another instead of duplicating it: `security/remediation` doesn't re-explain
  bug reports, it cites `qa/bug-reporting`.

Dependencies point one way — consumers → providers → `generalist`, which is
referenced 21 times and references nothing.

> **[See the full graphs in GRAPH.md →](GRAPH.md)**
> Rendered diagrams for all three layers, plus the load-bearing skills and the
> reference counts per agent.

## Structure

```
{agent-name}/
├── AGENTS.md          # identity, reasoning model, heuristics, limits
├── CORE.md            # (optional) condensed essence, inlined into children
└── skills/
    └── {skill-name}/
        └── SKILL.md   # Agent Skills spec: name, description+trigger, license
```

Skills are **not** loaded upfront. Each agent's `AGENTS.md` says when to load
each one — progressive disclosure keeps the base context small.

Referencing skills that ship *outside* this catalog (`react-19`, `playwright`,
`tailwind-4`, …) is done **by name and conditionally** — never by path. The
catalog installs into five tools with five different layouts, so a hardcoded
`~/.claude/skills/...` would be a lie in four of them.

---

## Provider support

| Tool | Agents land in | Skills land in |
|------|----------------|----------------|
| Claude Code | `~/.claude/agents/{name}.md` | `~/.claude/skills/{name}/` |
| opencode | `~/.config/opencode/agents/{name}.md` | `~/.config/opencode/skills/{name}/` |
| Kiro CLI | `~/.kiro/agents/{name}.json` | `~/.kiro/skills/{name}/` |
| Codex | *(no named-agent concept)* | `~/.codex/skills/{name}/` |
| Shared | — | `~/.agents/skills/{name}/` (read by opencode + Codex) |

`install.py` needs Python 3.9+ and has zero external dependencies. Adding a tool
means appending one `Tool(...)` to the `TOOLS` list.

You can also **reference** the catalog instead of copying it — see
[INTEGRATION.md](INTEGRATION.md) for the tradeoff.

---

## Docs

| File | What's in it |
|------|--------------|
| [AGENTS.md](AGENTS.md) | The catalog index and the conventions every agent follows |
| [INSTALL.md](INSTALL.md) | `install.py` guide — flags, conflicts, dependencies *(Spanish)* |
| [USAGE.md](USAGE.md) | Per-tool setup recipes, global and per-project *(Spanish)* |
| [INTEGRATION.md](INTEGRATION.md) | Wiring agents into a config by reference, not by copy |
| [REFERENCE_.md](REFERENCE_.md) | Quick human-facing orientation guide *(Spanish)* |

---

## License

[Apache-2.0](LICENSE) — see the `license` field in every `SKILL.md`.
