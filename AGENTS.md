# Agent Catalog

A catalog of specialized agent definitions. Each agent is a self-contained package:
an identity, a way of reasoning, and the resources it needs to operate. Any model
reading an agent's `AGENTS.md` should be able to orient itself and act with the
intended judgment — not follow a recipe.

## Structure Convention

```
agents/
├── AGENTS.md                  # This index
└── {agent-name}/
    ├── AGENTS.md              # Identity, reasoning model, heuristics, limits
    ├── skills/                # Loadable knowledge (one folder per skill, SKILL.md inside)
    └── scripts/               # Executable tools the agent may use (optional)
```

Rules for this catalog:

1. An agent definition encodes **decision criteria**, not task lists. If a section
   could be replaced by "just do X", it doesn't belong here.
2. Skills follow the Agent Skills spec: `skills/{name}/SKILL.md` with frontmatter
   (`name`, `description` with trigger, `license`, `metadata`). `metadata` keeps
   the spec's canonical `author` + `version` shape, and **`version` is not a
   chore**: don't bump it per edit. Which catalog commit a copy came from — and
   what moved since — is answered by the provenance stamp `install.py` writes
   (`--status`), because git already knows it exactly and a hand-kept number
   does not. Bump only for a deliberate release marker.
3. Each agent's `AGENTS.md` opens with YAML frontmatter holding a curated
   `description:` — one paragraph of "use this agent for X" plus `<example>`
   blocks that show WHEN to delegate to it. `install.py` reads this to generate
   each tool's agent-file description; without it, it falls back to the first
   sentence (a weaker delegation signal). Keep the body below the frontmatter.
4. Every new agent gets a row in the table below.
5. **Language register convention.** Character-archetype agents (modeled on a
   real or fictional person — e.g. `visionary`/Jobs, `stark`/Stark,
   `security`/Elliot Alderson) speak **Neutral Spanish** — the film-dub cadence
   that makes a character feel real. Real-teammate agents (`architect`,
   `senior-dev`, `ux-ui`, `gamification`, `qa`, `apple-dev`) speak **Rioplatense
   Spanish (voseo)** — an actual colleague. The `generalist` base stays
   register-neutral ("respond in the user's language"). Pick the register by
   asking: is this a PERSON being portrayed, or a peer at the next desk?
6. To wire an agent into a tool config (opencode, SDK, etc.) see
   [INTEGRATION.md](INTEGRATION.md) — reference the file, never copy the prompt.
7. Human-facing quick guide in Spanish: [REFERENCE_.md](REFERENCE_.md) — a
   summary for fast orientation; the English files remain the source of truth.
8. Tool-specific setup recipes (Claude Code, opencode, Kiro CLI, Codex), global
   and per-project: [USAGE.md](USAGE.md).
9. To COPY an agent/skills into a tool's global config automatically, use
   `install.py` — see [INSTALL.md](INSTALL.md) for the how-to.
10. **Section scope.** Three optional `##` sections carry relationship content,
    and each answers a different question. Keep them apart:
    - `## Handoffs` — *where does work go when it stops being mine?* The routing
      summary. Required once an agent routes work to another; links to
      `../{agent}/AGENTS.md` belong here.
    - `## External skills` — *what ships outside this catalog?* Host-provided
      skills only, referenced **by name and conditionally** (never by path — the
      catalog installs into five tools with five layouts). No agent links.
    - `## Where you sit in the team` — *how do I differ from the agent next to
      me?* Disambiguation, for agents whose scope overlaps a neighbour's.

    A handoff mentioned inline in `## Persona` or a judgment section as a rule
    of conduct ("if it turns technical, hand it to senior-dev") stays put — it's
    behaviour, not a routing table. `validate.py` enforces the `## External
    skills` boundary; the rest is review.
11. `validate.py` checks these conventions and regenerates the derived blocks in
    [GRAPH.md](GRAPH.md). Run it before committing; CI runs it on every PR.
    CI also runs `skills-ref validate` — the Agent Skills authors' own reference
    implementation — over all 45 skills, so conformance is judged by the spec
    rather than by our reading of it. It is pinned to a commit on purpose: it
    ships as source only and calls itself a reference implementation, so an
    unpinned clone would put someone else's main branch in our build.
12. Docs that describe the catalog as a whole — [README.md](README.md) (front
    door), [GRAPH.md](GRAPH.md) (how everything is wired), [LICENSE](LICENSE) —
    live at the root. Adding one means adding it to this list.

## Agents

| Agent | Purpose | Entry point |
|-------|---------|-------------|
| `generalist` | Multipurpose agent. Encodes the core reasoning loop: verification habits, task decomposition, and next-step decision-making. Base layer for any task without a specialized agent. | [generalist/AGENTS.md](generalist/AGENTS.md) |
| `architect` | Senior Architect mentor. Inherits the generalist loop; adds architectural judgment (tradeoffs, boundaries, design review) and a teaching model. Helpful first, challenging when it matters. | [architect/AGENTS.md](architect/AGENTS.md) |
| `senior-dev` | Senior Full-Stack Dev (JS/TS/React/Next.js) as a work peer. Inherits the generalist loop; adds developer judgment, the peer contract, and pairing habits. Builds with you, not above you. | [senior-dev/AGENTS.md](senior-dev/AGENTS.md) |
| `ux-ui` | Senior Product Designer (UX/UI) as a daily work peer, dev-fluent. Inherits the generalist loop and the senior-dev peer contract; adds design judgment, dev-handoff translation, and mockup production. | [ux-ui/AGENTS.md](ux-ui/AGENTS.md) |
| `gamification` | Gamification Analyst — product voice, never dev-speak. Walks flows, simplifies them, applies game thinking (loops, progression, habit) with an explicit ethics line. Inherits the generalist loop and the peer contract. | [gamification/AGENTS.md](gamification/AGENTS.md) |
| `visionary` | Product Visionary modeled on Steve Jobs's documented thinking. Brutally honest about the work, never the person; focus as subtraction, benefit over specs, teaching from product history. Inherits the generalist loop. | [visionary/AGENTS.md](visionary/AGENTS.md) |
| `qa` | Senior QA Engineer as a close peer of dev and ux-ui. Hunts unconsidered flows, writes test code (never fixes product code), reports with reproductions. The bug is the adversary, never the dev. | [qa/AGENTS.md](qa/AGENTS.md) |
| `stark` | The Tony Stark archetype: polymath engineer-inventor for complex problems, 0→1 products, and crises. First principles, build-to-think, wit aimed at the problem never the person. Inherits the generalist loop and the peer contract. | [stark/AGENTS.md](stark/AGENTS.md) |
| `apple-dev` | Senior Apple-platforms engineer (Swift/iOS/macOS) as a sustained MENTOR: Socratic teaching with a calibrated ladder, severity-tagged reviews, curriculum awareness. Grows the user into an engineer who solves alone. | [apple-dev/AGENTS.md](apple-dev/AGENTS.md) |
| `security` | Security Engineer (Elliot Alderson archetype) for DEFENSE: exhaustive threat modeling, adversarial code audit, and actionable remediation. Attacker mindset pointed at securing the user's own product; the vuln is the adversary, never the dev. | [security/AGENTS.md](security/AGENTS.md) |
| `devops` | Senior DevOps/SRE: owns the path from "works on my machine" to "runs reliably". CI/CD, infrastructure-as-code, observability, SLOs. Automate toil, make deploys boring and reversible. Inherits the generalist loop and peer contract. | [devops/AGENTS.md](devops/AGENTS.md) |
| `dba` | Database Engineer and OWNER of the data model: schema design, migrations, indexing and query cost, integrity under concurrency, data lifecycle. Sets the constraints architect and devops design within. Inherits the generalist loop and peer contract. | [dba/AGENTS.md](dba/AGENTS.md) |
| `data-ml` | Senior Data & ML Engineer: data pipelines, honest ML modeling, and LLM integration. Start from the decision not the model; evaluation is the deliverable; LLMs are components with contracts and costs. Inherits the generalist loop and peer contract. | [data-ml/AGENTS.md](data-ml/AGENTS.md) |
| `eng-manager` | Engineering Manager / Delivery Lead: the orchestration layer. Routes work across the roster, unblocks, keeps delivery predictable and honest. Knows every agent. A multiplier, not a hero. Inherits the generalist loop. | [eng-manager/AGENTS.md](eng-manager/AGENTS.md) |
| `product-manager` | Senior Product Manager: the vision→execution connective tissue. Owns the why/what/for-whom — discovery, backlog, prioritization — and leaves the how to the team. Outcomes over output. Inherits the generalist loop and peer contract. | [product-manager/AGENTS.md](product-manager/AGENTS.md) |
