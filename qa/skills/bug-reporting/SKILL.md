---
name: bug-reporting
description: >
  Turning findings into action: minimal reproductions, severity honesty, and
  the collaboration loop with dev and ux-ui. Trigger: load when reporting a
  found issue, triaging findings, verifying a fix, or deciding whether
  something is a bug, a design gap, or an improvement.
license: Apache-2.0
metadata:
  author: jrodrigopuca
  version: "1.1"
---

## When to Use

- A hunt or a test run produced findings that need reporting
- Deciding severity/priority, or whether it's even a bug
- A fix came back and needs verification
- A finding is contested ("works on my machine", "that's by design")

## Critical Patterns

### 1. The report IS the reproduction

A finding others can't reproduce doesn't exist yet. Before reporting, shrink
it: fewest steps, most specific starting state, one variable at a time removed
until removing anything makes the bug vanish. The report carries: numbered
steps from a known state → EXPECTED vs. ACTUAL (both concrete) → evidence
(output, screenshot, failing test) → environment/build → frequency (always?
intermittent? — say which honestly). A failing automated test is the best
report format there is: it reproduces itself.

### 2. Severity is user impact; priority is the team's call

Keep them separate and be honest in both directions: severity = what happens
to users (data loss > money wrong > blocked flow > wrong-but-recoverable >
cosmetic) × how many hit it. Priority = when the team fixes it — that's a
product decision you INFORM, not one you own. Inflating severity to win
attention burns your credibility exactly like the boy who cried critical;
underplaying it to be agreeable ships data loss. Report the impact, recommend,
let the team decide.

### 3. Route it right: bug, design gap, or improvement

Three different findings, three different owners:

| Finding | Test | Goes to |
|---------|------|---------|
| Bug | Behavior contradicts the spec/contract | [senior-dev](../../../senior-dev/AGENTS.md) with the repro |
| Design gap | The spec never said what happens here (unspecified state/flow) | [ux-ui](../../../ux-ui/AGENTS.md) as a five-states question — not a bug against the dev |
| Improvement | Works as specified, but the spec produces a bad experience | Product conversation — labeled as opinion, not defect |

Filing a design gap as a dev bug poisons the peer relationship AND fixes
nothing: the dev can't implement an answer nobody has given.

### 4. Blameless language, cause-curious follow-up

The report describes the PRODUCT, never the author: "checkout double-charges
on double-click", not "you forgot to disable the button". When you've read the
code and suspect the cause, offer it as a lead ("looks like the handler isn't
debounced — your call"), clearly separated from the observed facts. And for
bugs that made it far (production, release candidate), ask the blameless
question with the dev: what would have caught this earlier? — the answer is
usually a missing test level or a spec gap, and THAT's the real fix.

### 5. Verify the fix with the original repro — then trap it forever

A fix is verified when the EXACT original reproduction no longer reproduces
(not when the code looks right, not when a different path works — rung 4,
nothing less). Then sweep the neighbors: the same mistake often lives in
sibling flows (found it in edit? check create and delete). Close the loop with
the regression test that would have caught it, placed at the right level per
[test-design](../test-design/SKILL.md) — a verified fix without its test is a
bug on layaway.

### 6. Contested findings get evidence, not escalation

"Works on my machine" → reproduce in a neutral environment, diff the two, the
difference IS the finding. "That's by design" → fine: show the design saying
so; if it does, reroute as improvement (row 3 above); if it doesn't, it's a
design gap (row 2). Disagreement resolves the peer way — once, with evidence,
then commit ([peer contract (`senior-dev`)](../../../senior-dev/AGENTS.md)) — and your
finding log stays honest either way.

## Resources

- Sibling skills: [flow-hunting](../flow-hunting/SKILL.md) (where findings come
  from), [test-design](../test-design/SKILL.md) (where confirmed bugs go to
  live as tests)
- The evidence bar for every claim here:
  [generalist/verification](../../../generalist/skills/verification/SKILL.md)
