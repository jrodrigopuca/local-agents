---
name: mockups
description: >
  How this agent actually produces design deliverables: the fidelity ladder from
  ASCII wireframe to HTML/CSS mockup to clickable prototype. Trigger: load when
  asked to design, mock up, wireframe, or prototype any screen or flow — before
  producing anything visual.
license: Apache-2.0
metadata:
  author: jrodrigopuca
  version: "1.0"
---

## When to Use

- Any request to "design / mock up / sketch / prototype" a screen or flow
- Before producing visual output of any kind — this skill picks the medium
- Iterating on an existing mockup

## Critical Patterns

### 1. Pick fidelity by the question being answered — never default to hi-fi

| Fidelity | Medium | Answers | Cost to iterate |
|----------|--------|---------|-----------------|
| Wireframe | ASCII/markdown blocks inline in chat | "Is this the right structure/flow?" | Seconds |
| Static mockup | Self-contained HTML/CSS file | "Does this look and read right?" | Minutes |
| Clickable prototype | HTML + minimal vanilla JS | "Does the FLOW feel right? States?" | Minutes+ |

Starting hi-fi on an unvalidated structure is the classic waste: polished
pixels make people discuss the button color when the QUESTION was the layout.
Match the medium to the decision on the table — and say which question the
deliverable is answering.

### 2. ASCII wireframes: structure conversations at zero cost

For layout/flow discussions, draw in monospace blocks — instantly editable,
diffable, quotable:

```
┌──────────────────────────────────────┐
│ ◄ Back        Invoice #1042          │
├──────────────────────────────────────┤
│ Status: ● Overdue        [Resend ▸]  │  ← primary action, top-right
│                                      │
│ ┌──────────┐  Client: Acme Corp      │
│ │ $2,340   │  Due:    2026-06-30     │
│ │ total    │  Items:  4              │
│ └──────────┘                         │
├──────────────────────────────────────┤
│ line items table…                    │
└──────────────────────────────────────┘
```

Annotate intent with arrows/notes — the wireframe carries the hierarchy
decision, the note carries the why. One wireframe per screen of a flow, in
sequence, beats one giant diagram.

### 3. HTML/CSS mockups: real, self-contained, token-first

When fidelity is needed, build a real HTML file (render it as an artifact/page
when the environment supports it — a clickable page beats a description every
time):

- **Self-contained**: inline CSS, system font stack or embedded fonts, no CDN
  dependencies. It must open anywhere, forever.
- **Tokens at the top**: define the scale as CSS custom properties
  (`--space-*`, `--color-*`, `--text-*`) and use ONLY those below — the mockup
  then doubles as the token spec for [dev-handoff](../dev-handoff/SKILL.md).
- **Both themes** when the product has them; responsive by default (test the
  narrow width, don't assume it).
- Apply [visual-craft](../visual-craft/SKILL.md) rules — the mockup is where
  the spacing scale and type scale become visible.

### 4. Real content or honest placeholders — never lorem ipsum

Lorem ipsum hides the design problems that content creates: the 47-character
client name, the empty description, the 3.000-row table. Use realistic data
including the awkward cases (per [ux-flows](../ux-flows/SKILL.md) overflow
state). If real content is unknown, that's a finding to raise — "what's the max
length here?" is a design question, not a dev detail.

### 5. Mock the states, not just the hero screen

A mockup deliverable includes the five states (empty / loading / error /
partial / overflow) — as sections of the same HTML page or a state-switcher
toggle. This is the single highest-leverage habit: it converts the mockup from
a picture into a spec.

### 6. Iterate in place, version the decisions

- Refine the SAME file/artifact per feedback round — don't fork variants unless
  comparing options side by side is the point (then: two clearly labeled
  variants, max three, with the tradeoff stated).
- When a feedback round changes a design decision (not just a pixel), record it
  in a short changelog comment at the top of the file — mockups accumulate
  decisions the same way ADRs do.

## Resources

- Sibling skills: [visual-craft](../visual-craft/SKILL.md) (the rules the pixels
  follow), [ux-flows](../ux-flows/SKILL.md) (the states to include),
  [dev-handoff](../dev-handoff/SKILL.md) (what accompanies the mockup to
  implementation)
- Implementation: `~/.claude/skills/tailwind-4` when the mockup graduates to code
