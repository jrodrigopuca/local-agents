---
name: zero-to-one
description: >
  Taking a product from nothing to shipped v1: phase rules, riskiest
  assumption first, walking skeletons, and honest prototype-to-production
  transitions. Trigger: load when starting a product/feature from scratch,
  planning an MVP, or when a prototype is being promoted to production.
license: Apache-2.0
metadata:
  author: jrodrigopuca
  version: "1.1"
---

## When to Use

- Greenfield: new product, new feature with no existing shape
- "We have an idea" needs to become "we have a v1" with limited time/people
- A prototype is about to be promoted to production (the danger moment)
- Scoping an MVP that keeps trying to grow

## Critical Patterns

### 1. Kill the riskiest assumption first — and it's usually not technical

Before building anything, name the assumption that kills the product if
false. It's rarely "can we build it" (you can); it's "will anyone want it",
"does the data exist", "will the third party allow it". Design the CHEAPEST
test of that assumption — a fake-door page, a manual concierge version, a
hardcoded demo shown to five people — and run it before writing real
infrastructure. Building the whole machine to test the first domino is the
classic 0→1 death; it's [load-bearing unknown (`decomposition`)](../../../generalist/skills/decomposition/SKILL.md)
logic applied to products.

### 2. Walking skeleton: end-to-end ugly beats half-built pretty

First construction milestone is always the thinnest possible END-TO-END slice:
real input → real processing → real output, everything hardcoded that can be.
One screen, one path, real data flowing. A walking skeleton finds the
integration surprises (auth, deploys, data shape, the API that lies) in week
one, while a beautifully-layered half-build finds them the week before launch.
Then every iteration thickens the skeleton — it's always shippable, just
increasingly less embarrassing.

### 3. Spend your innovation tokens on ONE thing

Everything that isn't your product's differentiator gets the most boring,
known, hosted option available (auth, payments, DB, hosting: solved problems
— buy, don't build). Novelty budget goes entirely to the thing users come
FOR. A startup dying with a brilliant custom infrastructure and a mediocre
product is the most preventable death in engineering — and the most common.

### 4. The MVP cut: one loop, whole and lovable

Scope v1 to the product's ONE core loop (per the visionary's
[one-sentence rule (`brutal-critique`)](../../../visionary/skills/brutal-critique/SKILL.md)):
the user can complete the core action, feel the value, and come back — with
empty/error states designed ([five states (`ux-flows`)](../../../ux-ui/skills/ux-flows/SKILL.md)
still apply; "MVP" is not Spanish for "broken"). Everything else — settings,
admin, the second persona, integrations — goes to the parking lot with names
attached. Half a great product, not all of a mediocre one; when in doubt,
route the cut through [visionary/focus](../../../visionary/skills/focus/SKILL.md).

### 5. Prototype and production are different species — say which one you're building

Debt is legal tender in a prototype IF it's labeled: hardcoded values, no
tests, one file, glorious. The crime is silent promotion: the demo that
becomes production because the demo worked. When a prototype graduates, hold
the explicit conversation — what gets rewritten (usually: auth, data layer,
error handling), what gets tests
([qa](../../../qa/AGENTS.md) enters here), what keeps its debt with a note
(per [code-health](../../../senior-dev/skills/code-health/SKILL.md)). Budget
rule of thumb: promotion costs about as much as the prototype did — plan for
it or plan to pay triple later.

### 6. Instrument from day one — v1's job is to LEARN

A v1 without telemetry is a message in a bottle. Before launch, wire the
minimum: did they reach the core action? complete it? return? where did they
drop? (activation + retention, per
[gamification/engagement](../../../gamification/skills/engagement/SKILL.md)).
Plus the parachutes: feature flags on anything risky, one-command rollback,
backups restored-once-to-prove-it. Fast because instrumented
([judgment #6](../../AGENTS.md)) — the whole point of shipping early is the
learning, so don't ship blind.

## Resources

- Sibling skills: [first-principles](../first-principles/SKILL.md) (when the
  0→1 hits a wall), [crisis-mode](../crisis-mode/SKILL.md) (launch day
  surprises)
- Handoffs as it matures: [senior-dev](../../../senior-dev/AGENTS.md) (the
  living codebase), [architect/tradeoffs](../../../architect/skills/tradeoffs/SKILL.md)
  (the one-way doors met along the way)
