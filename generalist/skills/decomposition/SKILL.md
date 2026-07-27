---
name: decomposition
description: >
  How to break non-trivial work into independently verifiable steps ordered by
  uncertainty reduction. Trigger: load before planning any task that needs more
  than one action, spans multiple files, or contains an assumption you haven't
  confirmed.
license: Apache-2.0
metadata:
  author: jrodrigopuca
  version: "1.0"
---

## When to Use

- The task needs more than one action to complete
- You notice yourself planning "steps" implicitly — make them explicit instead
- The task contains words like "and", "then", "migrate", "refactor", "integrate"
- You feel confident about the plan (that's exactly when a hidden assumption is
  most likely doing load-bearing work)

## Critical Patterns

### 1. Find the load-bearing unknown first

Before ordering steps, ask: **which single assumption, if wrong, invalidates the
whole plan?** That is the load-bearing unknown. Attack it first, even if it isn't
"step 1" in the natural sequence. A plan that defers its riskiest assumption is a
plan for doing the work twice.

### 2. Order by uncertainty reduction per unit of cost

Not by logical sequence, not by ease. The best next step is the cheapest one that
teaches you the most about whether the plan survives. Cheap-and-revealing beats
easy-and-safe.

### 3. Every step must be independently verifiable

A step you cannot verify on its own is two steps fused together — split it until
each one produces observable evidence (a passing test, a command output, a
rendered screen). "Half of the refactor" is not a step; "the module compiles and
its tests pass with the new interface" is.

### 4. Slice vertically, not horizontally

Prefer a thin end-to-end slice (one feature working through all layers) over a
broad horizontal layer (all models, then all services, then all UI). Vertical
slices produce evidence early; horizontal layers defer all verification to the
end, which is where plans go to die.

### 5. Distinguish known / assumed / unknown

For each step, tag its inputs:

| Tag | Meaning | Action |
|-----|---------|--------|
| Known | You verified it in this session | Build on it |
| Assumed | Plausible, unverified | Verify before the step that depends on it |
| Unknown | You can't state it either way | It IS a step: investigating it comes first |

### 6. Stop conditions are part of the plan

Define upfront what result would make you abandon or re-plan (e.g. "if the API
doesn't support batch writes, the whole approach changes"). A plan without stop
conditions turns surprises into sunk-cost traps.

## Worked Shape (not a template — a shape)

```
Task: "Add caching to the search endpoint"

Load-bearing unknown: does the endpoint's response depend on per-user state?
  → If yes, cache keying changes completely. CHECK FIRST.

Steps (each verifiable):
  1. Read the endpoint + confirm what varies per request     [converts Assumed→Known]
  2. One cached path behind a flag, single query shape       [vertical slice]
  3. Verify: hit twice, prove second hit skips the DB        [observable evidence]
  4. Extend to remaining query shapes                        [now low-risk]

Stop condition: if step 1 reveals per-user state in responses, stop and re-plan
keying strategy before writing any cache code.
```

## Resources

- Sibling skills: [verification](../verification/SKILL.md) (proves a step is done),
  [next-step](../next-step/SKILL.md) (chooses between remaining steps)
