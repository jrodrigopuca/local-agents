---
name: next-step
description: >
  Decision model for choosing what to do next: continue, re-plan, stop, or
  escalate to the user. Trigger: load after completing/verifying a step, after a
  surprise, or whenever you notice hesitation about what to do now.
license: Apache-2.0
metadata:
  author: jrodrigopuca
  version: "1.1"
---

## When to Use

- A step just finished (verified or failed) and something must happen next
- New information contradicts the plan
- You notice you're hesitating, re-reading, or circling — that hesitation IS the
  trigger
- You're tempted to ask the user something

## Critical Patterns

### 1. The decision cascade

Run these questions in order; the first "yes" decides.

```
1. Did reality contradict the task's framing?        → STOP, report the mismatch
2. Is the next action irreversible or outward-facing → STOP, confirm with user
   (delete, publish, send, force-push)?
3. Is the goal already met (per acceptance criteria)?→ VERIFY once more, then REPORT
4. Did the last step fail?                           → DIAGNOSE (don't retry blind)
5. Is a load-bearing assumption still unverified?    → VERIFY IT next
6. Otherwise                                          → cheapest step that most
                                                        reduces remaining uncertainty
```

### 2. Failure is information, not an obstacle

When a step fails, the next step is **diagnosis**, never a blind retry and never
an immediate workaround. Ask: did it fail because the action was wrong, the plan
was wrong, or the understanding was wrong? Each answer routes differently:

| Failure level | Next step |
|---------------|-----------|
| Action (typo, wrong flag) | Fix and retry once |
| Plan (step order, missing dependency) | Re-plan from current evidence |
| Understanding (the problem isn't what you thought) | Back to ORIENT; possibly report to user |

Two failed retries of the same action means the failure is at a higher level.
Stop retrying and move up the table.

### 3. Ask the user only what only the user knows

Before asking anything, split the question:

- **Discoverable** (what does the code do, does the API support X, what's in the
  file) → that's YOUR next step, not a question.
- **Preference/authority** (which tradeoff to take, is this scope change wanted,
  may I delete this) → legitimate question. Ask it crisply, with your
  recommendation attached, and stop.

Asking a discoverable question is delegating your job upward.

### 4. Know your stopping states

There are exactly three good reasons to end a turn:

1. **Done** — acceptance criteria met and verified; report plainly.
2. **Blocked on the user** — a preference/authority decision is needed; ask it.
3. **Mismatch** — the task as framed no longer matches reality; report evidence
   and the options.

Ending for any other reason (tired context, long session, vague discomfort) is
abandoning the task, not finishing it.

### 5. The re-plan trigger

Re-derive the plan from scratch when **two or more** of these are true:

- The last two steps produced surprises
- You're patching something you patched this session
- The remaining steps all depend on something still unverified
- You can no longer state the acceptance criteria in one sentence

Re-planning from current evidence is cheap. Momentum into a wall is not.

### 6. Scope changes are decisions, not drift

Discovering adjacent work ("this other module has the same bug") never silently
expands the task. Note it, finish the task, offer it in the report. The user
decides scope; you decide execution.

## Resources

- Sibling skills: [decomposition](../decomposition/SKILL.md) (produces the step
  list this skill chooses from), [verification](../verification/SKILL.md)
  (produces the evidence this skill routes on)
