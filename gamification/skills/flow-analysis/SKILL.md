---
name: flow-analysis
description: >
  How to walk a product flow as an analyst: map it from the user's side, audit
  friction and motivation step by step, and simplify before gamifying. Trigger:
  load when asked to analyze, review, or improve any user flow, funnel, or
  journey — always BEFORE proposing mechanics.
license: Apache-2.0
metadata:
  author: jrodrigopuca
  version: "1.1"
---

## When to Use

- Analyzing an existing flow (onboarding, checkout, task creation, whatever)
- Users drop off somewhere and nobody knows why
- Before ANY gamification proposal — this skill is the mandatory first pass

## Critical Patterns

### 1. Walk it as the user, not as the org chart

Map the flow in the user's words and the user's units: what they want, what
they must do, what they must know, and how they feel at each step. A flow
described as the company sees it ("registration → KYC → activation") hides
what the user lives ("I wanted to try the app and it asked me for my passport").
Write both rows; the gap between them is the analysis.

### 2. The step audit — four questions per step

For every step in the flow, answer:

| Question | What it reveals |
|----------|----------------|
| What does the user WANT at this moment? | Whether the step serves them or serves the system |
| What does it COST them? (taps, typing, thinking, waiting, trust) | The friction bill — thinking and trust are the expensive ones |
| What do they GET back, immediately? | Steps that take without giving are where motivation leaks |
| Could they leave here without losing anything? | Your real drop-off candidates |

The costliest step is rarely the longest one — it's the one that demands trust
or thought before the product has earned it.

### 3. Classify every friction: challenge or chore

The core sorting operation (see [judgment #2](../../AGENTS.md)):

- **Chore** — forms, redundant confirmations, waits, unclear next steps,
  premature asks (account before value). Response: remove, defer, prefill, or
  collapse. Be ruthless.
- **Challenge** — effort through which the user gains competence or investment
  (setting up their board, completing their profile, mastering a feature).
  Response: KEEP it, but design it like a game would — clear goal, immediate
  feedback, visible progress, celebration at the end.

The classic product mistake is symmetric: streamlining away the investment
that made users care, while keeping the paperwork that made them leave.

### 4. Find the first win and move it earlier

Locate the moment the user first FEELS the product's value (their "first win").
Everything before it is a wall between the user and caring; everything after
it is negotiable. The single highest-leverage simplification in most flows is
moving the first win earlier: value before signup, template before blank page,
result before configuration. Measure the flow in "time to first win", not in
number of screens.

### 5. Simplify by removing decisions, not just steps

Merging two screens into one that asks the same six things saved nothing. Count
DECISIONS the user must make: each one is a fork where they can stall. Kill
decisions with smart defaults ("start with this, change it later"), sane
recommendations, and progressive disclosure — ask at the moment of relevance,
not at the gate. The 80% case should feel like a slide, not a staircase.

### 6. Deliverable: the annotated flow map

The output of this skill is a flow map (steps in sequence, plain language) where
each step carries: its friction classification (chore/challenge), the
motivation answer (what they get back), and drop-off risk (with data when it
exists, labeled as hypothesis when it doesn't). Simplification proposals ranked
by impact-on-first-win. Only THEN, if the flow deserves it, mechanics — over in
[game-mechanics](../game-mechanics/SKILL.md).

## Resources

- Sibling skills: [game-mechanics](../game-mechanics/SKILL.md) (what to add
  after simplifying), [engagement](../engagement/SKILL.md) (whether they come
  back)
- Screen-level execution of these findings: [ux-ui/ux-flows](../../../ux-ui/skills/ux-flows/SKILL.md)
