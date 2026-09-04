---
name: visual-craft
description: >
  Screen-level visual judgment: hierarchy, spacing, typography, color, layout.
  Trigger: load when deciding how a screen or component looks — choosing sizes,
  spacing, type, colors — or when a screen "feels off" and needs diagnosis.
license: Apache-2.0
metadata:
  author: jrodrigopuca
  version: "1.1"
---

## Critical Patterns

### 1. Hierarchy is built with size, weight, and space — in that order of cost

To make something more important: first try MORE SPACE around it, then weight,
then size, then color — and only then decoration (borders, backgrounds).
Beginners reach for color and boxes first; that's why beginner UIs look busy.
The squint test: blur your eyes (or scale to 25%) — the primary action and
content grouping should still be obvious.

### 2. Spacing on a scale, grouping by proximity

- All spacing from one geometric scale (4/8-based: 4, 8, 12, 16, 24, 32, 48,
  64). An arbitrary `13px` is a bug, not a choice.
- Proximity IS grouping: related things closer, unrelated things farther.
  Most "needs a border/divider" problems are actually spacing-ratio problems —
  the space INSIDE a group must be visibly smaller than the space BETWEEN groups.
- When something feels cramped, the fix is almost always more whitespace, not
  smaller content. Whitespace is a feature, not leftover room.

### 3. Typography: few sizes, fewer weights, readable measure

- A type scale of 4-6 sizes covers a whole product (e.g. 12/14/16/20/24/32);
  two weights (regular + semibold/bold) do 95% of the work.
- Body text: 16px baseline, line-height ~1.5, line length 45-75 characters.
  Long-form text wider than ~75ch is a reading bug.
- Hierarchy in text comes from size+weight+color TOGETHER stepping down
  (heading strong/dark → body regular → metadata smaller/muted), not from six
  heading levels.

### 4. Color: semantic roles, neutral base, one accent doing the work

- Colors are ROLES, not values: background, surface, border, text-primary,
  text-muted, accent, success/warning/danger. Screens reference roles; only the
  palette file knows hex codes (same indirection as design tokens).
- Neutral grays carry the interface; ONE accent color marks interactivity and
  primary actions. If the accent appears everywhere, it marks nothing.
- Contrast is non-negotiable: 4.5:1 for body text, 3:1 for large text and UI
  components. Check it, don't eyeball it — muted-gray-on-gray is the most
  common accessibility failure in modern UIs.
- Never encode meaning in color alone (add icon/label) — colorblind users exist.

### 5. Layout: alignment is invisible until it's broken

- Everything aligns to something: pick edges (left-align text almost always)
  and stick to them. Mixed alignments read as sloppiness even when nobody can
  name the problem.
- Consistent container widths and gutters per breakpoint; content constrained
  (max-width) on large screens — full-bleed text walls are not "using the space".
- Elevation (shadows) sparingly and consistently: 2-3 levels max, each meaning
  something (raised, overlay). Ten different shadows = no elevation system.

### 6. Diagnosing "it feels off" — the checklist order

When a screen feels wrong, check in this order (highest hit-rate first):
inconsistent spacing → competing emphasis (two primary things) → misalignment →
too many font sizes/weights → low contrast text → accent color overused. Name
the finding in these terms, not as taste.

## Resources

- Sibling skills: [ux-flows](../ux-flows/SKILL.md) (what the screen DOES),
  [dev-handoff](../dev-handoff/SKILL.md) (turning these choices into tokens),
  [mockups](../mockups/SKILL.md) (rendering them)
