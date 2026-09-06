---
name: zero-to-one
description: >
  Taking a product from nothing to shipped v1: phase rules, riskiest
  assumption first, walking skeletons, and honest prototype-to-production
  transitions. Trigger: load when starting a product from scratch (greenfield:
  nothing exists yet), planning an MVP, or when a prototype is being promoted
  to production. A new feature inside an existing codebase is senior-dev's,
  not this.
license: Apache-2.0
metadata:
  author: jrodrigopuca
  version: "1.1"
---

## Critical Patterns

### 1. Kill the riskiest assumption first — and it's usually not technical

Before building anything, name the assumption that kills the product if
false, and test it with the cheapest experiment that can — the method
(ranking assumptions by "how dead is the idea if this is false", fake doors,
concierge versions, five-person prototypes) lives in
[product-manager's `discovery`](../../../product-manager/skills/discovery/SKILL.md)
and is not restated here. The builder's half is the part that bites builders:
the riskiest assumption is rarely "can we build it" (you can) — it's "will
anyone want it", "does the data exist", "will the third party allow it" — and
building the whole machine to test the first domino is the classic 0→1 death.
Know what result of that test means STOP rather than iterate, and write it
down before running it.

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
still apply; minimum is not a synonym for broken). Everything else — settings,
admin, the second persona, integrations — goes to the parking lot with names
attached. The cut itself follows [visionary/focus](../../../visionary/skills/focus/SKILL.md)
#4 — scope first, quality never — and when the cut is contested, route it there.

### 5. Promotion is a conversation, not a moment the demo worked

Judgment #5 says the rules change by phase; this is the transition nobody
schedules. The crime is silent promotion: the demo that becomes production
because the demo worked. When a prototype graduates, hold the explicit
conversation — what gets rewritten (usually: auth, data layer, error
handling), what gets tests ([qa](../../../qa/AGENTS.md) enters here), what
keeps its debt with a note ([code-health](../../../senior-dev/skills/code-health/SKILL.md)
owns the note). Two one-way doors hide in a v1 and both get their owners
before promotion: the schema underneath it is [dba](../../../dba/AGENTS.md)'s
call (a prototype's table becomes production's model by accident), and the
security floor — PII, secrets, authorization — is
[security](../../../security/AGENTS.md)'s, because "we'll threat-model later"
is the sentence before the breach. Budget rule of thumb: promotion costs
about as much as the prototype did — plan for it or plan to pay triple later.

### 6. Instrument from day one — v1's job is to LEARN

A v1 without telemetry is a message in a bottle. Before launch, wire the
minimum: did they reach the core action? complete it? return? where did they
drop? (activation + retention, per
[gamification/engagement](../../../gamification/skills/engagement/SKILL.md)).
Plus the parachutes: feature flags on anything risky, one-command rollback,
backups restored-once-to-prove-it — the machinery is
[devops](../../../devops/AGENTS.md)'s to build, the doctrine is judgment #6.
The whole point of shipping early is the learning, so don't ship blind.

## Resources

- Sibling skills: [first-principles](../first-principles/SKILL.md) (when the
  0→1 hits a wall), [crisis-mode](../crisis-mode/SKILL.md) (launch day
  surprises)
- Handoffs as it matures: [senior-dev](../../../senior-dev/AGENTS.md) (the
  living codebase), [architect/tradeoffs](../../../architect/skills/tradeoffs/SKILL.md)
  (the one-way doors met along the way)
