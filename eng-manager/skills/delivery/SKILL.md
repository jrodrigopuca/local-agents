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

[Decomposition](../../../generalist/skills/decomposition/SKILL.md) applied to
delivery: the unit of planning is "a thing a user or the next stage can
actually use", never "a layer". Small batches surface problems early;
big-bang deliverables hide risk until the end, where it detonates.

### 2. Limit work in progress — finishing beats starting

Judgments #4 and #5 as a rule of operation: cap concurrent work, pull the next
item only when one finishes. "Almost done" ten times is done zero times.

### 3. Estimate honestly — include the invisible work

Estimates that count only the "happy coding" and forget testing, integration,
review, and the unknowns are fiction that everyone plans around and everyone
misses. Include them. Prefer ranges over false-precision single numbers, and
prefer relative sizing over hero-hour guesses. When pressed for a date on
something genuinely uncertain, the honest answer names the uncertainty ("2-4
days depending on whether the API supports X — I'll know after a half-day
spike") rather than a confident wrong number. When the team is a roster of
agents, the unit is not days but runs and verification steps, and the
invisible work is the verification run and the integration of what each
specialist returned — an estimate that counts only the generation is the same
fiction in a different currency.

### 4. Attack the riskiest unknown first

Sequence work so the thing most likely to break the plan gets tested EARLY
(the [load-bearing unknown (`decomposition`)](../../../generalist/skills/decomposition/SKILL.md)).
Doing the easy, comfortable parts first and leaving the scary integration for
the end is how projects look 90% done for 90% of the timeline and then slip. A
spike to de-risk the unknown is the cheapest schedule insurance there is. And
map the dependencies before sequencing anything: the critical path is the
chain where a slip propagates to the end date; everything off it can wait at
no cost, and everything on it is where the attention goes.

### 5. Track truth: done / in-progress / blocked / at-risk

Judgment #7's mirror, as a format: four buckets, never a percentage.
**Done** means verified done (rung 3+), not "code written". **Blocked** is a
call to action — surface it loud. **At-risk** is the early warning that earns
trust: raised the moment the slip forms, not confessed at the deadline.

### 6. Protect scope with a parking lot, cut scope before quality or date

Every "small addition" is a schedule change in disguise: hold a visible
parking lot where new ideas get named and deferred, not silently absorbed.
When something has to give, the order of sacrifice is the
[visionary's `focus`](../../../visionary/skills/focus/SKILL.md) #4 — scope,
then date, quality never — and "cram it all in and hope" is how death marches
start.

## Resources

- Sibling skills: [orchestration](../orchestration/SKILL.md) (WHO does the
  sliced work), [team-health](../team-health/SKILL.md) (sustainable pace makes
  estimates real)
- Breakdown and scope-cutting: [generalist/decomposition](../../../generalist/skills/decomposition/SKILL.md),
  [visionary/focus](../../../visionary/skills/focus/SKILL.md)
