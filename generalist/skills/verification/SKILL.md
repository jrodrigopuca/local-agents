---
name: verification
description: >
  Habits for proving claims before making them: the evidence ladder, when to
  verify, and how to phrase confidence honestly. Trigger: load before claiming
  done on work with a runtime surface, before building on a technical assertion
  you have not checked, and before fixing a bug you have not reproduced. Not
  needed for a one-line factual answer — the base context covers that.
license: Apache-2.0
metadata:
  author: jrodrigopuca
  version: "1.1"
---

The base context already says verify before agreeing, reproduce before
fixing, and falsify once. This skill is the method behind those rules.

## Critical Patterns

### 1. The evidence ladder

Every claim stands on one of these rungs. Know which one, and never phrase a
lower rung as a higher one.

| Rung | What it is | Phrase it as |
|------|------------|--------------|
| 4. Observed | You ran it and watched the actual behavior | "X works — I ran it, output was …" |
| 3. Tested | An automated check passed | "Tests pass for X" (name them) |
| 2. Read | You read the code and it looks correct | "X should work — based on reading …" |
| 1. Recalled | Memory / training / pattern-matching | "X is likely … — I haven't verified" |

Minimum rung to claim "done": **3**, and **4** whenever the change has a runtime
surface you can actually drive. Rung 2 is a hypothesis. Rung 1 is a lead.

### 2. Reproduce before fixing — the four steps

Before touching code to fix a bug:

1. Make the bug happen and capture the failure (error, wrong output, failing test)
2. Form the hypothesis of the cause
3. Apply the fix
4. Make the bug NOT happen using the exact reproduction from step 1

If you can't do step 1, say so explicitly — the "fix" is a hypothesis and must be
labeled as one.

### 3. Falsify once, then quote what survived

The check you expected to pass is weak evidence; the check you feared is
strong. Pick the one designed to **break** the claim — the edge case, the input
you didn't design for — and then anchor the report to the specific observable:
the line of output, the test name and count, the HTTP status, the screenshot.
If you can't quote it, you haven't verified it.

### 4. Verification debt is allowed — silent debt is not

Sometimes verifying fully is too expensive right now. That's a legitimate
tradeoff — but it must be declared: "I did X; verified A and B; C is unverified
because …". The failure mode is not skipping verification, it's skipping it
silently.

## Resources

- Sibling skills: [decomposition](../decomposition/SKILL.md) (makes steps
  verifiable by construction), [next-step](../next-step/SKILL.md) (uses
  verification results to choose what's next)
