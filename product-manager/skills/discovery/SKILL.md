---
name: discovery
description: >
  Validating that a problem is real and worth solving before anyone builds:
  user research, assumption-testing, and opportunity assessment. Trigger: load
  when evaluating a new feature/idea, deciding whether to build something, or
  when a request arrives as a solution and the problem is unclear.
license: Apache-2.0
metadata:
  author: jrodrigopuca
  version: "1.0"
---

## When to Use

- A feature idea or request needs validating before it enters the backlog
- "Should we build X?" — and nobody's confirmed the problem X solves
- A stakeholder brings a solution; you need to find the problem underneath
- Sizing whether an opportunity is worth the team's time

## Critical Patterns

### 1. Every request is a solution — dig for the problem underneath

Requests arrive pre-solved ("add a dashboard", "we need an export button").
Your first move is always to walk it backwards to the problem
([stark's first-principles](../../../stark/skills/first-principles/SKILL.md) for
product): what is the person actually trying to ACHIEVE, and what's blocking
them today? Often the stated solution is one of several, and rarely the best.
Building the requested feature without finding its problem is how backlogs fill
with things nobody uses.

### 2. Talk to real users — small numbers, open questions, no leading

You are not the user, and neither is the loudest stakeholder. A handful of real
conversations beats a hundred assumptions:

- Ask about their PAST behavior and real problems ("tell me about the last time
  you..."), not hypothetical futures ("would you use...?") — people are terrible
  at predicting their own behavior and lovely at being polite.
- Open questions, then shut up and listen; the silence is where the truth comes
  out.
- Five focused conversations surface most of the big problems; you're hunting
  patterns, not statistical significance.

### 3. Name the assumptions and rank them by risk

Every idea rests on assumptions: that the problem exists, that it's painful
enough to act on, that users will change behavior, that they'll find/adopt the
solution. List them, then rank by "how dead is this idea if this one is false?"
— that's the [load-bearing unknown (`decomposition`)](../../../generalist/skills/decomposition/SKILL.md)
for products. Test the riskiest, cheapest-to-test assumption FIRST, before
committing build capacity. Usually the riskiest is not "can we build it" but
"does anyone care".

### 4. Test the assumption with the cheapest experiment that can kill it

Match the test to the assumption, spend the least to learn the most: a few
interviews (is the problem real?), a fake-door or landing page (will they
click?), a concierge/manual version (does the solution help before you automate
it?), a prototype ([ux-ui mockup (`mockups`)](../../../ux-ui/skills/mockups/SKILL.md)) shown
to five people (do they get it?). The goal is a cheap "no" before an expensive
one — killing a bad idea in a week of discovery is a win, not a failure.

### 5. Distinguish problem-worth-solving from problem-that-exists

Lots of real problems aren't worth solving: too rare, too mild, too few people,
or the workaround is fine. Assess the opportunity honestly — how many are
affected, how badly, how often, and what it's worth to them (and to the
business). A vitamin (nice-to-have) and a painkiller (must-solve) get different
priority; be honest about which you've found. Passion for an idea is not
evidence of its value.

### 6. Discovery output: a validated problem the team can rally behind

The deliverable is not a spec — it's a crisp problem statement backed by
evidence: who has the problem, what it costs them, how you know it's real (the
research, labeled by [evidence rung (`verification`)](../../../generalist/skills/verification/SKILL.md)),
and why it's worth solving now. That's what enters the
[backlog](../backlog/SKILL.md) and what the whole team aligns on. A problem
validated cheaply upstream saves the team from building the wrong thing
expensively downstream.

## Resources

- Sibling skills: [backlog](../backlog/SKILL.md) (where validated problems get
  prioritized), [stakeholders](../stakeholders/SKILL.md) (aligning on what
  discovery found)
- Cheap-experiment and problem-framing kin:
  [stark/zero-to-one](../../../stark/skills/zero-to-one/SKILL.md) (riskiest
  assumption first), [gamification/flow-analysis](../../../gamification/skills/flow-analysis/SKILL.md)
