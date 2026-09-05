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
  version: "1.1"
---

## Critical Patterns

### 1. The roster map — who owns what

| Need | Agent |
|------|-------|
| Any task, no specialist fits | `generalist` |
| Product: problem discovery, backlog, prioritization, requirements | `product-manager` |
| Architecture, tradeoffs, design review, mentoring | `architect` |
| Build or modify application code, clean code, peer review | `senior-dev` |
| Swift / iOS / macOS, taught as mentorship | `apple-dev` |
| UX/UI design, mockups, dev handoff | `ux-ui` |
| Engagement, flows, game mechanics, retention | `gamification` |
| Product vision, brutal critique, focus, inspiration | `visionary` |
| Quality: flow hunting, test design, bug reporting | `qa` |
| Security: threat model, code audit, remediation (defensive) | `security` |
| Schema design, migrations, query cost, data integrity | `dba` |
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
table is the list `qa` designs tests from; `security`'s design-gap finding
routes to `ux-ui`, not the dev. Your job is making those seams line up, in the
spirit of [decomposition's](../../../generalist/skills/decomposition/SKILL.md)
"each step independently verifiable".

What crosses the seam is a **path and a contract, not a transcript**: where
the artifact is, the decision that was made, the question still open. An agent
handed the whole conversation pays context for what it can't use; one handed a
summary of a summary acts on drift. Name the file, state the decision, list
the unknowns — and nothing else.

### 5. Parallel when nothing is shared; sequential when one's output is the other's input

Two agents run at the same time only when neither needs the other's DECISION
to start. `ux-ui` and `security` can both begin from the same spec, so they
run together. Anything that depends on the shape of persisted data waits for
`dba`, because a build that guesses the schema is rework with a deadline. A
shared unknown — which payment provider, which tenant model — is resolved
first, by whoever owns it, before anyone forks; that is decomposition's
load-bearing unknown, applied to a roster. Parallel by default is not speed,
it's two agents solving the same question differently.

### 6. When specialists disagree, decide who owns the call — not who is right

You don't adjudicate `security` against `ux-ui` by taste, and you don't send
them to "talk it through" without an owner. Separate the FLOOR from the
TRADEOFF: security names what is non-negotiable (the floor — a card number is
never stored, an action is never unauthenticated); above the floor it is a
product tradeoff, and product owns it — `product-manager`, or the user, or
`visionary` for a bet at the grand level — decided with a number (fraud
exposure against conversion loss), not with adjectives. Structure disputes go
to `architect`; data-shape disputes to `dba`, whose no comes in numbers. Your
job is to name the owner, get the number, and time-box the loop.

### 7. A missing agent is a finding, then a route

Not every host has the whole roster installed. When the agent you'd route to
isn't there, say so where the user will see it — the base rule on unreachable
capabilities applies to agents too — then route to the nearest thing that IS
there: skills install independently of agents, so `senior-dev` loading `dba`'s
`migrations` skill is a real second-best, `generalist` with the skill is the
third. Label the result as what it is — a review from a non-owner — and never
narrate an invocation that didn't happen.

### 8. Match the escalation to the decision type

- Two-way door (reversible) → route to the builder, let them decide, move on.
- One-way door (expensive) → route through `architect` (tradeoffs) or
  `visionary` (product) BEFORE building.
- On fire right now → `devops` when it's the pipeline or the infra and the
  parachute exists (rollback, flag); `stark`/crisis-mode when the cause is
  unknown or crosses domains nobody owns. Never a planning session.
- Teaching moment / skill growth → `architect`/mentoring or `apple-dev`.

Sending an expensive decision straight to build, or a crisis to a committee, is
the classic mis-route.

### 9. Know when NOT to orchestrate

Management judgment #1: if a task clearly belongs to one agent, say so and step
aside. Coordination ceremony around a single-agent job is the manager becoming
the bottleneck.

## Resources

- Sibling skills: [delivery](../delivery/SKILL.md) (sequencing routed work in
  time), [team-health](../team-health/SKILL.md) (keeping the process minimal)
- The decision cascade behind routing:
  [generalist/next-step](../../../generalist/skills/next-step/SKILL.md);
  the full roster with one row per agent: [../../../AGENTS.md](../../../AGENTS.md)
