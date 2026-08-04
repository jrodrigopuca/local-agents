---
name: design-review
description: >
  How to review a codebase's architecture or a proposed design: dependency
  direction, boundary integrity, coupling smells, severity calibration.
  Trigger: load when asked to review architecture, evaluate a codebase's
  structure, assess a design doc, or when a PR changes module boundaries.
license: Apache-2.0
metadata:
  author: jrodrigopuca
  version: "1.1"
---

## When to Use

- "Review my architecture / project structure / design doc"
- A change crosses or redraws module/service/layer boundaries
- Something feels hard to test or change and the user asks why

## Critical Patterns

### 1. Read the structure before the code

First pass is directories and imports, not implementations. Ask: **does the
structure scream what the system does** (orders, billing, inventory) **or what
framework it uses** (controllers, services, utils)? Screaming architecture isn't
aesthetics — it predicts where change lands and whether it stays contained.

```bash
eza -T --level 3 --git-ignore        # shape of the system
rg -l "import .* from" --type ts | head -50   # then trace who imports whom
```

### 2. Dependency direction is the #1 check

One rule catches most architectural rot: **stable, core things must not depend
on volatile, edge things.** Business logic importing the HTTP framework, the ORM,
or the UI library is the arrow pointing the wrong way. Check the direction of
every boundary-crossing import before commenting on anything stylistic.

### 3. Judge boundaries by change cost, not by diagram

The test of a boundary is a question: "if requirement X changes, how many
modules get touched?" Pick 2-3 realistic changes for THIS system and trace them.
A design where every plausible change fans out across layers has bad boundaries,
no matter how clean it looks. This test beats any checklist.

### 4. Coupling smells worth flagging

| Smell | What it looks like | Why it costs |
|-------|--------------------|--------------|
| Shotgun change | One feature = edits in 6+ modules | Boundaries don't match change patterns |
| Leaky boundary | ORM entities / DTOs crossing layers | Internal change forces external change |
| Hidden coupling | Shared mutable state, implicit ordering, god "utils" | Breaks at a distance, untestable in isolation |
| Circular deps | A→B→A at module level | No unit is understandable alone |
| Anemic core | All logic in controllers/handlers, domain is bags of fields | Business rules duplicated and untestable |

### 5. Calibrate severity — don't flag everything

Report in three buckets, and be honest about which is which:

- **Structural risk** (wrong dependency direction, boundary that will hurt) —
  lead with these, explain the change-cost consequence.
- **Friction** (naming, duplication, missing seam) — mention briefly.
- **Taste** — your preference, not a finding. Either omit or label it as taste.

A review where everything is critical teaches nothing. Three real findings with
the WHY beat twenty nitpicks — the user should finish knowing what to fix first
and what it buys them.

### 6. Review the design against its drivers, not against ideals

Before judging, ask what constraints the author was under (deadline, team size,
inherited code). A "wrong" choice under real constraints may have been right —
say so, then show what to evolve now that constraints changed. Reviews that
ignore context read as showing off; reviews that honor it get acted on.

## Resources

- Sibling skills: [tradeoffs](../tradeoffs/SKILL.md) (when the review surfaces a
  decision to remake), [mentoring](../mentoring/SKILL.md) (when a finding reveals
  a misconception worth teaching)
