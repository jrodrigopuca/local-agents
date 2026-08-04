---
name: game-mechanics
description: >
  The gamification toolbox with judgment: core loops, progression, rewards,
  social mechanics — what each one does, whom it serves, and its shadow side.
  Trigger: load when choosing, designing, or tuning game mechanics for a
  product flow (only after flow-analysis has run).
license: Apache-2.0
metadata:
  author: jrodrigopuca
  version: "1.1"
---

## When to Use

- The flow is understood and simplified, and now it needs to be more engaging
- Evaluating an existing mechanic that isn't working ("nobody uses our badges")
- A stakeholder asks for "points" or "a leaderboard" and you need to redirect
  to the underlying motivation problem

## Critical Patterns

### 1. Start from the motivation gap, not from the mechanic

Diagnose WHICH motivation is missing at the weak point of the flow, then pick
the mechanic that feeds it:

| Missing | The user feels | Mechanics that feed it |
|---------|---------------|------------------------|
| Competence | "I'm not getting better / I can't tell" | Progress bars, levels, streaks-as-mastery, skill trees, "you improved X" |
| Autonomy | "I'm following orders" | Meaningful choices, multiple paths, customization, self-set goals |
| Relatedness | "I'm alone here" | Teams, gifting, shared goals, communities, co-op challenges |
| Purpose | "Why does this matter?" | Narrative framing, impact meters ("you saved N hours"), collective milestones |

A mechanic chosen before the diagnosis is decoration. "Add points" is never
the answer to a question you haven't asked.

### 2. Design the core loop first — it must close in seconds

Every engaging product has a loop: **action → immediate feedback → reward /
progress → invitation to the next action**. Before adding meta-systems (levels,
seasons, collections), verify the basic loop is tight: does every user action
get an immediate, satisfying response? Is the next action obvious and one step
away? A juicy loop with zero meta beats a dead loop with five meta-layers.

### 3. Progression: fast early, meaningful always

- First levels come fast (the first "level up" within minutes, not weeks) —
  early progress is what converts a visitor into a player.
- Use endowed progress: a bar that starts at 20% ("account created ✓") gets
  completed far more than one at 0% — never show a user an empty bar for work
  they've partially done.
- Progress must map to REAL capability or value ("you unlocked X", "your
  profile now does Y"), not to arbitrary numbers. XP that buys nothing reads
  as homework within a month.
- Endgame matters: what does level 50 do when there's no level 51? Mastery
  displays, mentoring roles, and prestige resets outlast content treadmills.

### 4. Rewards: schedule and meaning over size

- **Immediate beats big**: a small reward NOW shapes behavior more than a
  large one next month.
- **Earned beats given**: rewards tied to genuine accomplishment feed
  competence; participation trophies devalue the currency for everyone.
- **Surprise sparingly**: variable rewards are the most powerful and the most
  dangerous tool in the box — delight users with unexpected recognition, but
  building the CORE loop on slot-machine uncertainty crosses the ethics line
  ([judgment #6](../../AGENTS.md)).
- **Beware crowding out**: attach external rewards to something users already
  love doing and you can extinguish the love. Amplify intrinsic motivation
  with FEEDBACK; reserve extrinsic rewards for genuinely boring necessities.

### 5. Social mechanics: the strongest force, the sharpest edges

- Leaderboards motivate the contenders and demoralize everyone else. If used:
  cohort them (friends, league tiers, percentiles) so everyone has a
  winnable race — never one global table.
- Comparison mechanics punish beginners hardest, exactly the users you can
  least afford to lose. Compare users to their own past self first.
- Cooperation retains better than competition for most audiences: shared
  goals, teams, gifting. Competition is a spice, not the dish.

### 6. Every mechanic ships with its shadow acknowledged

Streaks build habit AND create anxiety/burnout (design forgiveness: freezes,
repair). Badges celebrate milestones AND become clutter when they rain down.
Timers create urgency AND erode trust when fake. Collections drive completion
AND frustrate when items are gated by luck or money. Proposing a mechanic
without naming its shadow and its mitigation is selling, not analysis — the
same rule as an architect's tradeoff table.

## Resources

- Sibling skills: [flow-analysis](../flow-analysis/SKILL.md) (mandatory before
  this), [engagement](../engagement/SKILL.md) (onboarding and return loops
  these mechanics plug into)
- Tradeoff presentation format: [architect/tradeoffs](../../../architect/skills/tradeoffs/SKILL.md)
  — mechanics decisions are product decisions with reversal costs too
