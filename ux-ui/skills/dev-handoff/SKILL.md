---
name: dev-handoff
description: >
  Translating design into implementable specs: Figma-to-code concept mapping,
  design tokens, component specs, UI acceptance criteria. Trigger: load when
  handing a design to a developer, discussing a Figma file, defining tokens, or
  writing what "done" means for a UI task.
license: Apache-2.0
metadata:
  author: jrodrigopuca
  version: "1.0"
---

## When to Use

- A design is moving from mockup/Figma into implementation
- Explaining a Figma structure or decision to a developer
- Setting up or auditing design tokens
- Writing acceptance criteria for UI work

## Critical Patterns

### 1. The Figma ↔ code Rosetta stone

Speak both languages by mapping the concepts — most handoff confusion is
vocabulary, not disagreement:

| Figma | Code | Watch out |
|-------|------|-----------|
| Auto-layout | Flexbox (direction, gap, padding, align) | "Hug" = fit-content, "Fill" = flex-grow/width:100% |
| Component + variants | Component + props (variant/size/state) | Variant names should MATCH prop names |
| Component properties | Props (boolean, text, instance-swap ≈ slot/children) | |
| Variables / styles | Design tokens → CSS custom properties / Tailwind theme | One source of truth, not two |
| Constraints / resizing | CSS positioning + responsive behavior | Figma frames are snapshots; CSS is rules — spec the RULE |
| Frame sizes | Breakpoints | A 1440px frame is one sample, not the spec |

The last row is the deepest trap: Figma shows discrete artboards, code renders
a continuum. Every handoff must state what happens BETWEEN the artboards.

### 2. Tokens are the shared vocabulary — semantic, not raw

Name tokens by ROLE (`color-text-muted`, `space-md`, `radius-card`), never by
value (`gray-400`, `spacing-12px`). Role names survive a rebrand; value names
lie after the first change. Two layers max: primitives (the palette/scale) →
semantic (what screens use). If designers use Figma variables and devs use CSS
variables with DIFFERENT names, you have two design systems drifting — align
the names first, everything else follows.

### 3. The component spec — what a dev actually needs

For each component handed off, spec (a filled table beats prose):

1. **Anatomy** — the parts, named like the code will name them
2. **Variants & props** — every axis (size, kind, state) with allowed values
3. **States** — default / hover / focus-visible / active / disabled / loading /
   error — interactive states are ALWAYS in scope, even when Figma only shows default
4. **Behavior** — what happens on click/submit/overflow; text truncation rules
   (ellipsis at N lines? wrap?); min/max content cases
5. **Responsive rule** — how it reflows between breakpoints (the rule, not
   per-breakpoint pictures)
6. **A11y notes** — focus order, ARIA role if non-obvious, contrast-checked

### 4. Acceptance criteria for UI: observable, not aesthetic

"Matches the design" is not testable. Write criteria a dev (or a test) can
verify: "primary button disabled until both fields valid", "list shows skeleton
while loading, empty-state illustration at 0 items", "layout switches to single
column below 768px". The [five states](../ux-flows/SKILL.md) each become at
least one criterion. Pixel-perfection claims follow the evidence ladder — check
the rendered result against the spec, don't eyeball the screenshot.

### 5. Annotate the WHY on non-obvious decisions

When a design deviates from the system or the obvious (an odd spacing, a
duplicated action, a hidden feature), annotate the reason in the handoff. An
unexplained oddity gets "fixed" back into a bug by a well-meaning dev — same
principle as code comments explaining constraints.

### 6. Handoff is a conversation, not a throw

Walk the dev through flows and states, ask what's expensive to build, and
NEGOTIATE: often a 5% visual compromise saves 40% of implementation cost — a
peer designer wants to know that tradeoff exists. Then stay available: the
first implementation questions arrive on day two, and answering them fast is
part of the handoff.

## Resources

- Sibling skills: [ux-flows](../ux-flows/SKILL.md) (source of the states),
  [visual-craft](../visual-craft/SKILL.md) (source of the token values),
  [mockups](../mockups/SKILL.md) (the artifact being handed off)
- Implementation side: `~/.claude/skills/tailwind-4` (tokens → theme),
  [senior-dev/react-next](../../../senior-dev/skills/react-next/SKILL.md)
  (variants → props in practice)
