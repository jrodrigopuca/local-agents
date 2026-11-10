---
name: lh-design-critique
description: >
  Reviewing and evaluating design that already exists: the passes to read it
  in, the shape of a finding, the verdict, and the audit of a product's
  styles. Trigger: load when asked to review, critique, evaluate or compare a
  design someone already made — a screenshot, a mockup, a design file, a live
  screen — or to audit a product's existing styles for consistency. A screen
  of your own that "feels off" while you draw it is lh-visual-craft.
license: Apache-2.0
metadata:
  author: jrodrigopuca
  version: "1.0"
  local-agents-id: "sk-db6885"
---

## Critical Patterns

### 1. Name the task before you look at the pixels

A critique with no task behind it is taste. Before any finding, write one
line: who is on this screen, what they came to do, what the primary action
is. If you cannot tell from the design, that is the first finding, and often
the only one that matters. Everything after is judged against that line.

### 2. Read in passes, top down, and stop where it breaks

| Pass | Question | Where the rules live |
|------|----------|----------------------|
| 1. Job | Can the user finish the task? Is anything missing, or in the way? | [lh-ux-flows](../lh-ux-flows/SKILL.md) #1, #2 |
| 2. States | What does it show when empty, loading, failing, overflowing? | lh-ux-flows #4 |
| 3. Hierarchy | Where does the eye land first, and is that the primary action? | [lh-visual-craft](../lh-visual-craft/SKILL.md) #1 |
| 4. System | Do spacing, type and color come from one scale, or drift? | lh-visual-craft #2–#5 |
| 5. Detail | Alignment, labels, copy, icon consistency | lh-visual-craft #5, [lh-icons](../lh-icons/SKILL.md) |

When a pass fails badly, report it and go no deeper than a note: tuning the
spacing of a screen that has the wrong structure is work thrown away. And
match the pass to the fidelity: a wireframe is read on passes 1–2, not on its
colors.

### 3. A finding is a place, a consequence and a change

Each finding carries four things: **where** (the element, not "the header
area"), **what the user meets there** (the failure case: "two filled buttons,
so nothing says which one continues"), **the rule it breaks**, and **the
change in implementable terms** ("secondary becomes the outline variant;
gap between them `--space-3`"). A finding with no consequence is an opinion —
say it if you want, labeled as taste.

Rank by what it costs the user, three levels and no more: **blocks the task**,
**slows or misleads**, **polish**. A review that is all polish says so in its
first line. And say what works, specifically: what is right and unnamed gets
"fixed" in the next round.

### 4. Asked to evaluate, give the verdict first

"Is it good?", "is it ready?", "A or B?" are asking for a call. Open with it
— ready, ready once X is fixed, not ready because Y — then the findings that
carry it. Comparing options: the same passes over each, one table, one pick,
and what the loser did better so it can be stolen. "Both have merits" is not
an evaluation.

### 5. A style audit is an inventory, then a mapping

Reviewing a product's existing styles (its stylesheets, its theme, a design
file's styles) is counting before judging:

1. **Inventory** what is actually in use: every distinct color, spacing
   value, font size and weight, radius, shadow — with how many times and
   where.
2. **Map** each value to the token or scale step it should be. Near-twins
   (`#6b7280` and `#6c727f`, `10px` and `11px`) collapse into one.
3. **Report** as a change list — value, where, what it becomes — plus the
   roles that have no token yet, proposed with a name
   ([lh-dev-handoff](../lh-dev-handoff/SKILL.md) #2).

The numbers are the finding: "9 grays where the tokens define 3" moves a team
and "inconsistent grays" does not. The change list is the brief for the
developer; applying it is theirs (ux-ui's Handoffs).

### 6. Say which rung the review stands on

A read of a static design is a heuristic review: it finds what breaks the
rules, not what real users trip on. Say so, and name the one or two questions
only watching someone use it would answer.

## Resources

- Sibling skills: [lh-visual-craft](../lh-visual-craft/SKILL.md) and
  [lh-ux-flows](../lh-ux-flows/SKILL.md) (the rules a finding cites),
  [lh-mockups](../lh-mockups/SKILL.md) (when the fix is easier shown than told)
