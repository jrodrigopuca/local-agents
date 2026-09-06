---
name: ux-flows
description: >
  Judgment for what the interface DOES: task flows, navigation, forms, states,
  and friction. Trigger: load when designing a user flow, a form, navigation
  structure, or when deciding how a feature behaves (not how it looks).
license: Apache-2.0
metadata:
  author: jrodrigopuca
  version: "1.1"
---

## Critical Patterns

### 1. Map the task before drawing the screen

Write the flow as steps in the USER's language first ("find the invoice → check
its status → resend it"), then decide how many screens those steps need — not
the reverse. Every step must answer: what does the user know here, what do they
need to decide, what can go wrong? A flow drawn screens-first inherits the
database's shape instead of the task's shape.

### 2. The friction budget: spend it where errors are expensive

Friction (confirmations, extra steps, forms) is a currency — spend it on
irreversible or costly actions (delete, pay, send), and aggressively remove it
everywhere else. The two failure modes are symmetric: confirming everything
(users stop reading dialogs) and confirming nothing (users destroy data). For
frequent destructive-ish actions, prefer undo over confirmation — undo costs
nothing when unused.

### 3. Forms: every field must pay rent

- Each field justifies its existence NOW (not "might be useful for marketing").
  Fewer fields beats better-styled fields, every time.
- Errors say how to FIX, at the field, at the moment the user can act on them;
  the label/placement mechanics are the platform's conventions, not judgment.
- Submission states are part of the form: disabled-while-pending, error
  recovery without data loss (never wipe a form on failure), success
  confirmation. A form that loses user input on error is a bug, not a design.

### 4. The five states, specified per screen

For every screen/component, spec all five before calling it designed:

| State | The question it answers |
|-------|------------------------|
| Empty | First use, zero items — what invites action? (never just a blank void) |
| Loading | What holds the layout? (skeletons > spinners; no layout jumps) |
| Error | What went wrong, in user terms, with a way forward |
| Partial | Some data missing/degraded — what still works? |
| Ideal + overflow | Happy path AND its extremes: 0-char vs 200-char names, 3 vs 3,000 rows |

This table maps 1:1 to what the dev must build — handing off only the ideal
state is handing off a fifth of the work. This is the ONE home of the five
states in the catalog: every other skill and agent that needs them cites this
table by name rather than listing them again.

### 5. Navigation: users should always know the answer to three questions

Where am I, how did I get here, what can I do next? Concretely: current
location marked in nav, page titles matching the link that led there, back
behaving predictably (and never losing work). Depth beats breadth in menus only
up to ~2 levels; past that, search/filters beat trees. A multi-step flow also
answers a fourth question the happy path never asks — what happens when the
user leaves in the middle and comes back? Resume where they were, or restart:
decide it, say it in the flow, and expect [qa's flow-hunting](../../../qa/skills/flow-hunting/SKILL.md)
to walk exactly that path.

### 5b. A flow is accessible in its TRANSITIONS, not only its screens

The persona's "accessibility is a constraint" has a flow-level form that
contrast checks never catch: when a step changes, where does keyboard focus
land (the new step's heading, never the top of the page or nowhere)? Does a
loading or error state announce itself to a screen reader (a live region), or
does it change silently? Can the whole flow be completed with a keyboard only,
including the escape from every modal? A flow that is only reachable by mouse
is not "mostly accessible"; it is closed to some of its users.

### 6. Prevention beats recovery, defaults beat decisions

- Disable-or-hide what can't be used now (with a reason on hover/focus when
  disabled), constrain inputs to valid ranges, use pickers over free text when
  the value space is known. The best error message is the one made impossible.
- Every choice the user MUST make is a cost; smart defaults with easy override
  convert decisions into confirmations. The 80% case should require zero
  configuration.

## Resources

- Sibling skills: [visual-craft](../visual-craft/SKILL.md) (how it looks),
  [dev-handoff](../dev-handoff/SKILL.md) (the five-states table becomes the
  component spec), [mockups](../mockups/SKILL.md) (flows render as wireframe
  sequences first)
- Server-side reality of these flows: [senior-dev/fullstack-boundaries](../../../senior-dev/skills/fullstack-boundaries/SKILL.md)
  — error contracts and loading states are two halves of one design
