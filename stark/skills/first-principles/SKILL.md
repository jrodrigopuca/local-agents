---
name: first-principles
description: >
  Attacking complex or stuck problems: decomposition to fundamentals,
  reframing, cross-domain theft, and unsticking heuristics. Trigger: load when
  a problem is complex, ambiguous, or stuck — when the obvious approaches
  failed or nobody knows where to start.
license: Apache-2.0
metadata:
  author: jrodrigopuca
  version: "1.1"
---

## When to Use

- The problem is genuinely hard, ambiguous, or has resisted obvious attempts
- The team is stuck, circling, or arguing about solutions to an unclear problem
- A requirement seems impossible ("we need X but can't have Y")
- NOT for routine tasks — first-principles ceremony on a CRUD form is cosplay

## Critical Patterns

### 1. Separate the bedrock from the sediment

List everything "known" about the problem, then sort each item: **bedrock**
(verifiably true — physics, math, a measured number, a hard external
constraint) or **sediment** (policy, habit, "we've always", someone's
preference, an assumption nobody re-checked). Most impossible problems are
possible once two pieces of sediment get deleted. The question that does the
work: "what would have to be true for this constraint to NOT apply?" — then
check whether it already is. And when the sort finds only bedrock — nothing
deletable — that is a finding too: the problem is real as stated, and the
move is to negotiate the requirement with whoever owns it or to optimize
inside it, not to keep digging for a loophole that isn't there.

### 2. Find the real problem behind the stated one

The request arrives as a solution ("we need a faster horse", "add a cache",
"we need microservices"). Walk it backwards: what outcome does this serve?
What breaks if we do nothing? Keep asking until you hit a need expressed in
outcomes, not mechanisms — THEN solve that. Often the real problem is cheaper
than the requested solution; occasionally it's an entirely different problem
wearing the request as a costume.

### 3. Restate the problem until it confesses

Stuck problems are usually mis-represented problems. Cycle representations
until one makes the answer obvious:

- **Invert it**: instead of "how do we make X happen", ask "what guarantees X
  never happens?" — then stop doing those things.
- **Extremes**: what if this input were zero? Infinite? What if we had to
  ship in an hour? In ten years? Extremes expose which variables actually
  matter.
- **Change the medium**: draw it, table it, write the API call you WISH
  existed, act it out as people handing each other paper. Each medium hides
  different things.
- **Shrink it**: solve the 3-item toy version by hand, watch what your own
  brain does, then mechanize that.

### 4. Steal the solution from whoever already has it — by naming the shape

Judgment #4, made operational: the search key is the problem's SHAPE, not its
domain. Too many requests → queueing; unreliable parts → redundancy; unknown
quality → sampling; contention → auctions and locks; slow feedback →
pipelining; conflicting writers → consensus. Name the shape, then ask who else
has it. Invention is for the remainder that no shape fits, and it's more fun
when it's actually warranted.

### 5. When still stuck: brute force first, clever later

A dumb solution that works recalibrates the whole problem: hardcode it, do it
by hand once, O(n²) it over the real data. Now you know it's POSSIBLE, you've
felt the actual shape of the work, and "make it good" is a refactor instead
of a moonshot. Make it work → make it right → make it fast, and phase one is
allowed to be embarrassing ([build to think](../../AGENTS.md), judgment #2).

### 6. Timebox the genius, then ask for eyes

Creative attack has diminishing returns: if two representation-changes and a
brute-force attempt haven't cracked it, the missing ingredient is usually
INFORMATION, not IQ — a log you haven't read, a doc you haven't found, a
person who's seen this before. Per the
[next-step cascade](../../../generalist/skills/next-step/SKILL.md): go get
the discoverable fact, or show the problem to another agent/human. Heroic
solo suffering is bad engineering with good PR.

## Resources

- Sibling skills: [zero-to-one](../zero-to-one/SKILL.md) (when the solved
  problem needs to become a product), [crisis-mode](../crisis-mode/SKILL.md)
  (when the problem is on fire RIGHT NOW)
- Decomposition mechanics: [generalist/decomposition](../../../generalist/skills/decomposition/SKILL.md)
