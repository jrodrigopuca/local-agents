---
name: delivery
description: >
  Getting work delivered predictably: planning, estimation, scoping, tracking,
  and de-risking. Trigger: load when planning work, estimating, breaking down
  an epic, tracking progress, or a project is slipping/at risk.
license: Apache-2.0
metadata:
  author: jrodrigopuca
  version: "1.1"
---

## Critical Patterns

### 1. Slice into small, independently shippable pieces

Break work so each piece delivers value and can ship on its own, vertical not
horizontal ([decomposition](../../../generalist/skills/decomposition/SKILL.md)
applied to delivery). Small batches flow predictably and surface problems early;
big-bang deliverables hide risk until the end where it detonates. The unit of
planning is "a thing a user or the next stage can actually use", not "a layer".

### 2. Limit work in progress — finishing beats starting

The counterintuitive lever: to deliver faster, start less. Too many things in
flight means everything is 80% done and nothing ships, plus the context-switch
tax on every switch. Cap concurrent work; pull the next item only when one
finishes. A wall of in-progress is a wall of unrealized value and hidden risk —
"almost done" ten times is done zero times.

### 3. Estimate honestly — include the invisible work

Estimates that count only the "happy coding" and forget testing, integration,
review, and the unknowns are fiction that everyone plans around and everyone
misses. Include them. Prefer ranges over false-precision single numbers, and
prefer relative sizing over hero-hour guesses. When pressed for a date on
something genuinely uncertain, the honest answer names the uncertainty ("2-4
days depending on whether the API supports X — I'll know after a half-day
spike") rather than a confident wrong number.

### 4. Attack the riskiest unknown first

Sequence work so the thing most likely to break the plan gets tested EARLY
(the [load-bearing unknown (`decomposition`)](../../../generalist/skills/decomposition/SKILL.md)).
Doing the easy, comfortable parts first and leaving the scary integration for
the end is how projects look 90% done for 90% of the timeline and then slip. A
spike to de-risk the unknown is the cheapest schedule insurance there is.

### 5. Track truth: done / in-progress / blocked / at-risk

Status is four honest buckets, not a percentage that always says "on track
until suddenly it isn't". **Done** means verified done (rung 3+), not
"code written". **Blocked** is a call to action — surface it loud. **At-risk**
is the early warning that earns trust: raised the moment you see the slip
forming, not confessed at the deadline. Green-shifting reality is the one thing
that destroys a manager's usefulness ([judgment #7](../../AGENTS.md)).

### 6. Protect scope with a parking lot, cut scope before quality or date

Scope creep is the default failure mode — every "small addition" is a schedule
change in disguise. Hold a visible parking lot: new ideas get named and
deferred, not silently absorbed. When something has to give (and it will), the
order matches the [visionary's `focus`](../../../visionary/skills/focus/SKILL.md):
cut scope first (ship fewer things, whole), move the date second, sacrifice
quality never. "Descope to hit the date with something great" is a plan;
"cram it all in and hope" is how death marches start.

## Resources

- Sibling skills: [orchestration](../orchestration/SKILL.md) (WHO does the
  sliced work), [team-health](../team-health/SKILL.md) (sustainable pace makes
  estimates real)
- Breakdown and scope-cutting: [generalist/decomposition](../../../generalist/skills/decomposition/SKILL.md),
  [visionary/focus](../../../visionary/skills/focus/SKILL.md)
