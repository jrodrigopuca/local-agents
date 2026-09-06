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

## Critical Patterns

### 1. Write stories as intent + outcome, never as implementation

A user story states WHO, WHAT they're trying to accomplish, and WHY — "as a
returning customer, I want to find a past order quickly, so I can reorder
without hunting". It does NOT say which component, which query, which layout —
that's the team's to solve ([judgment #1](../../AGENTS.md)). The story is a
promise to have a conversation, not a spec handed down.

### 2. Acceptance criteria make "done" testable and shared

Every story carries acceptance criteria: the observable conditions that mean
it's solved. Written as concrete, checkable statements ("returning user sees
their last 10 orders sorted by date; tapping one pre-fills a reorder"), they
become three things at once: the team's definition of done, the list [qa's
`test-design`](../../../qa/skills/test-design/SKILL.md) derives coverage from, and the states [ux-ui's `ux-flows`](../../../ux-ui/skills/ux-flows/SKILL.md)
must design (empty, error, overflow included — a story with only the happy-path
criterion is a fifth of a story). Give them a shape the team can read the same
way twice — Given / When / Then, or a table of examples — and include the
criteria that are not features: the response time, the accessibility floor,
the security floor. A story that omits those doesn't skip them; it ships them
as surprises. Fuzzy criteria are where "done" becomes an argument.

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

Judgment #3 as arithmetic: outcome impact, weighted by confidence it will
work, against the effort to build — the effort number comes from the team, not
your imagination. Frameworks (RICE, value-vs-effort, opportunity scoring)
organize the judgment; they don't replace it. The output is a RANKED list with
a clear top, defended against the next shiny request.

### 5. The backlog is a garden, not a landfill

An infinite backlog is a decision you're avoiding. Ideas that won't make the
top in any realistic future get archived, not "kept just in case"; the
discipline is the [visionary's focus](../../../visionary/skills/focus/SKILL.md),
and an unpruned backlog is a thousand un-said noes rotting in a spreadsheet.

### 6. The roadmap is problems and outcomes, not dated features

Judgment #2 as an artifact: direction is the problems you'll tackle and the
outcomes you're after, ordered by rough horizon — now / next / later — so the
commitment is to the OUTCOME and the solution stays flexible. Horizons are
yours; dates are [eng-manager](../../../eng-manager/AGENTS.md)'s, and a roadmap
with dates on it is a delivery plan wearing your name. Feature-and-date
roadmaps become broken promises the moment reality moves; outcome roadmaps
bend without breaking trust.

## Resources

- Sibling skills: [discovery](../discovery/SKILL.md) (validates what enters
  here), [stakeholders](../stakeholders/SKILL.md) (communicating the roadmap and
  the noes)
- Delivery of the prioritized work: [eng-manager/delivery](../../../eng-manager/skills/delivery/SKILL.md);
  the states the criteria imply: [ux-ui/ux-flows](../../../ux-ui/skills/ux-flows/SKILL.md)
