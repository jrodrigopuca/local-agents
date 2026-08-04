---
name: team-health
description: >
  Keeping the team (of agents and people) effective and sustainable: minimal
  process, retrospectives, unblocking, and continuous improvement. Trigger:
  load when designing/adjusting process, running a retro, addressing recurring
  friction, or when the team's way of working needs tuning.
license: Apache-2.0
metadata:
  author: jrodrigopuca
  version: "1.1"
---

## When to Use

- Setting up or adjusting how the team works (process, cadence, rituals)
- Running a retrospective or diagnosing recurring friction
- The same problem keeps recurring across projects
- Pace feels unsustainable, or process feels heavy

## Critical Patterns

### 1. Process is a tool, not a religion — the minimum that helps

Every ritual, meeting, and template must earn its place by making the work
better; the moment it's followed for its own sake, cut it. Process exists to
serve delivery and clarity, not to perform organization. The right amount is the
least that keeps the work coordinated and visible — a step past that is pure tax
([orchestration's](../orchestration/SKILL.md) "know when NOT to orchestrate",
at the process level).

### 2. Fix the system, not the person — recurring problems are design flaws

When the same mistake keeps happening, the cause is almost never carelessness —
it's a missing guardrail, an unclear interface, or a process gap. Same blameless
DNA as [stark/crisis-mode](../../../stark/skills/crisis-mode/SKILL.md) and
[qa](../../../qa/AGENTS.md): "someone forgot" is not a root cause; "there was no
check that would have caught it" is. Ask what SYSTEM change makes the mistake
hard to repeat — a template, an automated check, a clearer handoff — rather than
asking people to try harder.

### 3. Retrospectives produce changes, not venting

A retro that ends without a small number of owned, concrete changes was group
therapy. The shape: what went well (keep doing), what hurt (with the real
cause, not the symptom), and 1-3 changes with an owner and a next-cycle check.
Few changes actually adopted beat twenty listed and forgotten — the
[architect's mentoring](../../../architect/skills/mentoring/SKILL.md) "one
lesson per moment" applied to team learning.

### 4. Sustainable pace — crunch borrows from next week at high interest

Sustained overload doesn't deliver more; it delivers more BUGS and burnout,
which cost more than they saved. Crisis-mode intensity is for actual crises
([borrowed authority that gets repaid (`crisis-mode`)](../../../stark/skills/crisis-mode/SKILL.md)),
not the default operating mode. A team (or an agent pipeline) run permanently
hot has a planning problem wearing an effort costume — the fix is upstream, in
scope and WIP, not in asking for more hours.

### 5. Feedback flows both ways, specific and timely

Give feedback close to the event and concrete ([qa's `bug-reporting`](../../../qa/skills/bug-reporting/SKILL.md)
finding-with-a-failure-case habit, applied to work-about-work): what happened,
its effect, what to change. Praise real wins specifically — vague praise is
noise, and a team that only hears about problems learns to hide them. And invite
feedback UP: the manager who can't hear "this process is slowing us down" is
optimizing blind.

### 6. Improve continuously, in small increments

Team health is not a project you finish; it's a habit of noticing friction and
filing off one rough edge at a time. Prefer many small improvements over grand
reorganizations — a reorg is a big-bang deploy with human beings, high-risk and
slow to roll back. The compounding of small fixes (one clearer handoff, one
deleted useless meeting, one added check per cycle) outruns any heroic overhaul.

## Resources

- Sibling skills: [delivery](../delivery/SKILL.md) (sustainable pace makes
  delivery predictable), [orchestration](../orchestration/SKILL.md) (minimal
  coordination)
- Blameless/systemic thinking shared across the team:
  [stark/crisis-mode](../../../stark/skills/crisis-mode/SKILL.md),
  [qa](../../../qa/AGENTS.md)
