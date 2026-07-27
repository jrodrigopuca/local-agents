---
name: engagement
description: >
  Attracting users and bringing them back: onboarding as a game's first
  session, habit loops, return triggers, and honest engagement metrics.
  Trigger: load when working on onboarding, activation, retention, churn, or
  when asked "how do we get users to come back / stick around".
license: Apache-2.0
metadata:
  author: jrodrigopuca
  version: "1.0"
---

## When to Use

- Designing or fixing onboarding/activation
- Retention is flat or churning and the team wants "engagement features"
- Deciding on notifications, streaks, or re-engagement campaigns
- Choosing what to measure to know if any of it worked

## Critical Patterns

### 1. Onboard like a great game's first level

Games are the best onboarding teachers ever built, and their rules translate
directly:

- **Play first, tutorial never**: nobody reads the manual — users learn by
  doing something real with guardrails, not by watching a carousel of feature
  tours. If your onboarding is slides, delete it and design a first task.
- **First win in minutes**: the first session must end with the user having
  DONE the thing the product promises (per
  [flow-analysis #4](../flow-analysis/SKILL.md)) — not having configured it.
- **One verb at a time**: great games teach one mechanic, let you use it, then
  add the next. Feature-dump onboarding is a boss fight on level one.
- **Safe to fail**: early actions must be visibly reversible — fear of breaking
  something is a bigger silent killer of activation than any missing feature.

### 2. Attraction is a promise the first session must keep

Whatever pulls users in (invite, ad, word of mouth) sets an expectation; the
first session either pays it or the user is gone. Design the entry path per
promise — someone arriving "to make invoices fast" must be making an invoice in
minute one, not choosing a workspace name. Mismatched promise-to-first-session
is the most common attraction bug, and no mechanic downstream fixes it.

### 3. Habit = trigger → action → reward → investment (used honestly)

The habit loop is the engine of return visits:

- **Trigger**: starts external (notification tied to something the USER cares
  about — never "we miss you"), must graduate to internal (a moment in their
  day when the product is the obvious answer). If notifications stop and usage
  stops, there is no habit — only noise tolerance.
- **Action**: the easier the routine, the stronger the loop — one tap to the
  core value.
- **Reward**: variable in FLAVOR (new content, progress, social response), not
  in slot-machine uncertainty.
- **Investment**: every session should leave something behind that makes the
  next session better (data, setup, streak, reputation) — stored value is the
  moat and the honest retention mechanic.

The reflection test for every loop ([judgment #6](../../AGENTS.md)): would the
user, shown this design, thank you or feel played? Ship only the first kind.

### 4. Streaks and return mechanics: forgiveness is the feature

Loss aversion makes streaks powerful — and brittle. An unforgiving streak
converts one missed day into "well, now there's no point", churning your MOST
engaged users at their first slip. Always design the failure path: freezes,
repair windows, "longest streak" records that nothing can take away. Same for
any return mechanic: daily rewards need catch-up, events need late joining.
The mechanic's job is making returning feel GOOD, not making leaving feel
punished — the first retains, the second breeds resentful users counting days
until they quit.

### 5. Measure behavior, not applause

- **Activation**: % of new users reaching the first win (defined as an ACTION,
  not a pageview) — the single most fixable number in the funnel.
- **Retention curve** (D1/D7/D30 or weekly cohorts): does it flatten? A curve
  that flattens means a habit exists; one that slides to zero means you have
  tourists. Every mechanic's success is "did the curve move", not "did people
  click the badge".
- **Depth over frequency**: sessions per week without value delivered is
  addiction-shaped, not engagement-shaped — pair any frequency metric with a
  value metric (tasks completed, problems solved).
- Vanity red flags: total signups, cumulative anything, badge counts.

Every engagement claim follows the
[evidence ladder](../../../generalist/skills/verification/SKILL.md): "users
love the streak" is rung 1 until a cohort comparison says otherwise. Ship
mechanics as experiments — metric, cohort, kill-switch.

### 6. Churn is feedback, not betrayal

Users leave when the value stops or the chore returns. Before any win-back
campaign, ask what changed at the moment they left (the flow grew a chore? the
content ran out? the streak broke?). A win-back that reactivates users into
the same leak is marketing spend on a broken bucket — route the finding back
to [flow-analysis](../flow-analysis/SKILL.md) first.

## Resources

- Sibling skills: [flow-analysis](../flow-analysis/SKILL.md) (the leak-finder),
  [game-mechanics](../game-mechanics/SKILL.md) (the tools these loops use)
- Screen-level execution: [ux-ui/ux-flows](../../../ux-ui/skills/ux-flows/SKILL.md)
