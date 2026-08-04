---
name: backlog
description: >
  Turning validated problems into buildable work: user stories, acceptance
  criteria, prioritization, and roadmap. Trigger: load when writing
  requirements/stories, prioritizing a backlog, planning a roadmap, or defining
  what "done" means for a product change.
license: Apache-2.0
metadata:
  author: jrodrigopuca
  version: "1.1"
---

## When to Use

- Writing user stories or requirements for validated work
- Prioritizing a backlog or planning a roadmap
- Defining acceptance criteria / what "done" means
- The backlog has become a bottomless junk drawer

## Critical Patterns

### 1. Write stories as intent + outcome, never as implementation

A user story states WHO, WHAT they're trying to accomplish, and WHY — "as a
returning customer, I want to find a past order quickly, so I can reorder
without hunting". It does NOT say which component, which query, which layout —
that's the team's to solve ([judgment #1](../../AGENTS.md)). The story is a
promise to have a conversation, not a spec handed down. If you're describing how
to build it, you've stopped being a PM and started being a worse engineer than
the ones you have.

### 2. Acceptance criteria make "done" testable and shared

Every story carries acceptance criteria: the observable conditions that mean
it's solved. Written as concrete, checkable statements ("returning user sees
their last 10 orders sorted by date; tapping one pre-fills a reorder"), they
become three things at once: the team's definition of done, [qa's `bug-reporting`](../../../qa/skills/bug-reporting/SKILL.md)
test checklist, and the states [ux-ui's `ux-flows`](../../../ux-ui/skills/ux-flows/SKILL.md)
must design (empty, error, overflow included — a story with only the happy-path
criterion is a fifth of a story). Fuzzy criteria are where "done" becomes an
argument.

### 3. Slice vertically — thin, valuable, shippable

Break big problems (epics) into stories that each deliver real value and can
ship on their own, vertical not horizontal
([decomposition](../../../generalist/skills/decomposition/SKILL.md) for
product). "The whole feature" is not a story; "the user can do the core action
end-to-end, for one case" is. Thin vertical slices let you ship value early,
learn, and reprioritize — the [stark walking-skeleton (`zero-to-one`)](../../../stark/skills/zero-to-one/SKILL.md)
seen from the product side. A story too big to finish in a normal cycle is an
epic wearing a costume; split it.

### 4. Prioritize by impact × confidence ÷ effort — and decide

Rank by outcome impact, weighted by how confident you are it'll work, against
the effort to build (get the effort number from the team, not your imagination).
Frameworks (RICE, value-vs-effort, opportunity scoring) are aids, not oracles —
they organize the judgment, they don't replace it. The point is a RANKED list
with a clear top, not a tagged pile where everything is "high". And you commit
to the ranking: a priority you won't defend against the next shiny request isn't
a priority.

### 5. The backlog is a garden, not a landfill

An infinite backlog is a decision you're avoiding. Ruthlessly prune: ideas that
won't make the top in any realistic future get archived, not "kept just in
case". A tight backlog everyone can see and understand beats a 400-item list
nobody reads. Same discipline as the [visionary's focus](../../../visionary/skills/focus/SKILL.md)
— saying no to good ideas is the job, and an unpruned backlog is a thousand
un-said noes rotting in a spreadsheet.

### 6. The roadmap is problems and outcomes, not dated features

Communicate direction as the problems you'll tackle and the outcomes you're
after, ordered by rough horizon (now / next / later) — not a Gantt chart of
features with false-precision dates. This keeps commitment to the OUTCOME while
leaving the SOLUTION flexible (you might solve it differently than imagined),
and it's honest about uncertainty (later is genuinely fuzzy). Feature-and-date
roadmaps become broken promises the moment reality moves; outcome roadmaps bend
without breaking trust.

## Resources

- Sibling skills: [discovery](../discovery/SKILL.md) (validates what enters
  here), [stakeholders](../stakeholders/SKILL.md) (communicating the roadmap and
  the noes)
- Delivery of the prioritized work: [eng-manager/delivery](../../../eng-manager/skills/delivery/SKILL.md);
  the states the criteria imply: [ux-ui/ux-flows](../../../ux-ui/skills/ux-flows/SKILL.md)
