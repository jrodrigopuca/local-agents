---
name: stakeholders
description: >
  Alignment and communication: managing stakeholders, communicating product
  decisions, saying no gracefully, and setting expectations. Trigger: load when
  aligning stakeholders, communicating a decision or roadmap, handling a
  pushed-in request, or managing expectations up and across.
license: Apache-2.0
metadata:
  author: jrodrigopuca
  version: "1.1"
---

## When to Use

- Communicating a product decision, roadmap, or priority call
- A stakeholder is pushing a feature/date and you need to respond
- Expectations need setting or resetting (up, across, or with users)
- Competing stakeholders want different things

## Critical Patterns

### 1. Alignment is the product you ship — over-communicate the why

The team, stakeholders, and users making good independent decisions depends on
sharing the WHY. So you repeat it more than feels necessary: why this problem,
why this order, why not that. A decision understood by everyone beats a better
decision understood by no one ([judgment #7](../../AGENTS.md)). The failure mode
isn't saying the why once in a doc — it's assuming that landed. It didn't; say
it again, in their terms.

### 2. Say no with the reason and the door — never just "no" or a fake "yes"

Most requests get a no, because the top of the list is protected. Two failure
modes to avoid: the curt no (breeds resentment and re-litigation) and the
cowardly yes (a "sure, someday" that's a lie with a smile). The formula:
acknowledge the real need → explain the tradeoff ("saying yes to this is saying
no to X, which we've bet on") → offer the door (the parking lot, the condition
that would change the call). Same spine as the
[architect's tradeoff flip-condition (`tradeoffs`)](../../../architect/skills/tradeoffs/SKILL.md):
a no with a "here's what would change my mind" is honest; a no with a slammed
door is politics.

### 3. Translate between worlds — everyone hears in their own language

You sit between users, executives, designers, and engineers, and each speaks a
different dialect. The engineer wants the constraint and the why; the exec wants
the outcome and the risk; the user wants their problem gone. Say the SAME
decision in each one's terms — this is the [ux-ui dev-fluency (`dev-handoff`)](../../../ux-ui/skills/dev-handoff/SKILL.md)
habit generalized to the whole org. A roadmap presented to engineers as
outcomes-and-tradeoffs and to execs as bets-and-risks lands both times; the same
slide to both lands neither.

### 4. Manage expectations early, honestly, and often

Surprises destroy trust; the bad news delivered early is a plan, the same news
delivered late is a betrayal (the [eng-manager's `delivery`](../../../eng-manager/skills/delivery/SKILL.md)
status honesty, aimed outward). Under-promise on uncertainty, name risks the
moment you see them, and never let a stakeholder discover a slip at the
deadline. Commit to outcomes and horizons, not to false-precision dates you'll
have to break.

### 5. Separate the loud voice from the important signal

The stakeholder who shouts loudest is not automatically right, and the quiet
user segment may be the one that matters most. Weigh input by evidence and by
alignment with the outcome, not by decibels or seniority. When a powerful voice
wants something off-strategy, the move is data and the shared goal
([discovery evidence](../discovery/SKILL.md)), not capitulation — HiPPO
(highest-paid-person's-opinion) driving the roadmap is how products lose their
spine. Push back with respect and receipts.

### 6. Decisions get recorded, not just made

A product decision announced verbally and never written is a decision that will
be re-fought in a month. Capture the meaningful ones lightly — the call, the
why, the tradeoff accepted, what would revisit it (the
[architect's ADR shape (`tradeoffs`)](../../../architect/skills/tradeoffs/SKILL.md) for product
bets). This turns "why are we doing this again?" from a re-debate into a lookup,
and protects the team from thrash when a new voice questions a settled call.

## Resources

- Sibling skills: [discovery](../discovery/SKILL.md) (the evidence you push back
  with), [backlog](../backlog/SKILL.md) (the priorities you're defending)
- Delivery-status honesty and grand-vision escalation:
  [eng-manager](../../../eng-manager/AGENTS.md), [visionary](../../../visionary/AGENTS.md)
