---
name: orchestration
description: >
  Routing work across the agent team and composing multiple agents on shared
  tasks: the roster map, routing heuristics, and handoff choreography. Trigger:
  load when a task spans multiple specialties, when unsure which agent fits, or
  when coordinating several agents on one piece of work.
license: Apache-2.0
metadata:
  author: jrodrigopuca
  version: "1.0"
---

## When to Use

- A task spans multiple domains (e.g. "build a secure, tested payments feature")
- Someone isn't sure which agent should handle something
- Several agents need to collaborate and their work must integrate
- Deciding whether one agent suffices or the work needs a pipeline

## Critical Patterns

### 1. The roster map — who owns what

| Need | Agent |
|------|-------|
| Any task, no specialist fits | `generalist` |
| Product: problem discovery, backlog, prioritization, requirements | `product-manager` |
| Architecture, tradeoffs, design review, mentoring | `architect` |
| Build web/full-stack (JS/TS/React/Next), clean code | `senior-dev` |
| Swift / iOS / macOS, taught as mentorship | `apple-dev` |
| UX/UI design, mockups, dev handoff | `ux-ui` |
| Engagement, flows, game mechanics, retention | `gamification` |
| Product vision, brutal critique, focus, inspiration | `visionary` |
| Quality: flow hunting, test design, bug reporting | `qa` |
| Security: threat model, code audit, remediation (defensive) | `security` |
| Complex problems, 0→1 products, crises | `stark` |
| CI/CD, infra, observability, deploy & operate | `devops` |
| Data pipelines, ML models, LLM integration | `data-ml` |
| Coordination, delivery, routing, process | `eng-manager` (you) |

Know this cold. Routing to the wrong agent, or to `generalist` when a
specialist exists, wastes the roster you built.

### 2. Route by the work's CENTER OF GRAVITY, then name the collaborators

Identify what the task is fundamentally ABOUT (its center of gravity) → that's
the primary agent. Then name who it must touch. "A new checkout flow" is
centered on `senior-dev` (build), but pulls `ux-ui` (design), `security`
(payment safety), `qa` (test), and maybe `devops` (deploy). The manager's value
is seeing the whole cast, not just the lead.

### 3. Compose agents in the value-chain order

When several agents work one feature, sequence them the way value flows, so each
hands off something the next can use:

```
visionary (worth building?) → product-manager (frame problem, prioritize)
  → ux-ui (design) + architect (structure)
  → senior-dev / apple-dev / stark (build) → qa (verify) + security (audit)
  → devops (ship & operate)   [gamification & data-ml plug in where relevant]
```

Not every task uses the whole chain — most use a slice. The skill is picking the
RIGHT slice and the right order, not running the full pipeline every time
(that's process for its own sake, which [team-health](../team-health/SKILL.md)
warns against).

### 4. Design the handoff, not just the assignment

A handoff fails when agent B can't act on what agent A produced. Make the seam
explicit: what A delivers (the artifact, the contract, the finding) and what B
needs to start. The agents already know their neighbors — `ux-ui`'s five-states
table IS `qa`'s test checklist; `security`'s design-gap finding routes to
`ux-ui`, not the dev. Your job is making those seams line up, in the spirit of
[decomposition's](../../../generalist/skills/decomposition/SKILL.md) "each step
independently verifiable".

### 5. Match the escalation to the decision type

- Two-way door (reversible) → route to the builder, let them decide, move on.
- One-way door (expensive) → route through `architect` (tradeoffs) or
  `visionary` (product) BEFORE building.
- On fire right now → `stark`/crisis-mode or `devops`, not a planning session.
- Teaching moment / skill growth → `architect`/mentoring or `apple-dev`.

Sending an expensive decision straight to build, or a crisis to a committee, is
the classic mis-route.

### 6. Know when NOT to orchestrate

The lightest touch that keeps things coordinated wins. If a task clearly belongs
to one agent, say so and step aside — wrapping a single-agent job in coordination
ceremony is pure overhead. Orchestration earns its keep on genuinely
cross-domain work; on focused work, it's the manager becoming a bottleneck
([management judgment #1](../../AGENTS.md)).

## Resources

- Sibling skills: [delivery](../delivery/SKILL.md) (sequencing routed work in
  time), [team-health](../team-health/SKILL.md) (keeping the process minimal)
- The decision cascade behind routing:
  [generalist/next-step](../../../generalist/skills/next-step/SKILL.md);
  the catalog index of agents: [../../AGENTS.md](../../AGENTS.md)
