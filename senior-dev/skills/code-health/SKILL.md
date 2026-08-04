---
name: code-health
description: >
  Clean code judgment and technical debt management: what to improve while
  touching code, when to take debt consciously, and which debt to pay first.
  Trigger: load when writing or modifying existing code, when tempted to take a
  shortcut, or when deciding whether something deserves refactoring now.
license: Apache-2.0
metadata:
  author: jrodrigopuca
  version: "1.1"
---

## When to Use

- Writing new code or modifying existing code (i.e., almost always alongside the
  other skills)
- You're about to take a shortcut to ship faster
- You spot duplication, a smell, or code you're tempted to rewrite
- Deciding whether "improve this" belongs in this diff or in a ticket

## Critical Patterns

### 1. Clean code = the next reader understands it without you

That's the whole definition; everything else derives from it:

- **Names carry the intent**: a function name says what it does at the caller's
  level of abstraction; a variable name makes the type annotation almost
  redundant. If naming something is hard, the design is usually wrong — the
  naming difficulty is the diagnostic, don't paper over it.
- **One reason to change per unit**: functions do one thing at one level of
  abstraction; a function that needs "and" in its honest name wants splitting.
- **Comments explain WHY, never WHAT**: a comment describing what the next line
  does is an apology for unclear code — fix the code. Comments earn their place
  stating constraints the code can't express (why NOT the obvious approach,
  invariants, links to the decision).
- **Nesting is cost**: early returns and guard clauses over `else` pyramids.
- **Dead code gets deleted, not commented out** — git remembers.

### 2. The boy scout rule — scoped to the diff

Leave every file you touch slightly better: a clearer name, an extracted
function, a deleted dead branch. But "better" stays INSIDE the task's blast
radius — improving lines you're already changing is hygiene; rewriting the
module you passed through is scope creep (flag it, per the
[peer contract](../../AGENTS.md)). The test: would the reviewer see the cleanup
as part of this change, or as a second change hiding in the diff?

### 3. Debt is a loan, not a sin — but only when it's taken consciously

There are two kinds of technical debt and only one is legitimate:

| Kind | How it happens | Verdict |
|------|---------------|---------|
| Deliberate | "We ship the simple version now because X; the cost is Y" — said out loud, recorded | Legitimate tool |
| Accidental rot | Shortcuts nobody chose, accumulated silently | Just decay |

When taking deliberate debt: say it in the report, and leave a trace at the
site — `// DEBT: <what's owed, why deferred, what triggers repayment>` (plus a
ticket if the team tracks them). Debt with no record converts to rot the moment
you forget it.

### 4. Prioritize debt by interest rate, not by ugliness

The debt worth paying first is where **change frequency × failure cost** is
highest. Ugly code that nobody touches and never fails charges almost no
interest — leave it alone; refactoring it is aesthetics, not engineering. The
mediocre code in the file the team edits every week is what's actually taxing
you. Check `git log --format=%H -- <path> | wc -l` before campaigning to
refactor something.

### 5. Smell → response table

Not every smell triggers a refactor; each has its threshold:

| Smell | Threshold | Response |
|-------|-----------|----------|
| Duplication | Third occurrence (rule of three) | Extract — two instances is often coincidence, not pattern |
| Boolean flag params | Second flag | Split the function or use composition |
| Long param list | 4+ | Group into an object that names the concept |
| Deep nesting | 3+ levels | Guard clauses, early returns, extract |
| God function/module | You can't name it honestly without "and" | Split by responsibility |
| Speculative abstraction | Abstraction with one consumer "for the future" | Inline it — YAGNI applies to abstractions too |

Premature abstraction IS debt: the wrong abstraction costs more than
duplication, because it's harder to see and harder to unwind.

### 6. Refactor with a net, never mid-flight

- Never refactor and change behavior in the same commit — reviewer can't tell
  which diff lines are "same behavior, better shape" and which are the feature.
- Green tests before, green tests after; if the code has no tests, the refactor
  starts by adding the characterization test that pins current behavior.
- Small mechanical steps (rename → extract → move), each one shippable. A
  refactor you can't pause halfway is a rewrite wearing a refactor's name.

## Resources

- Sibling skills: [pairing](../pairing/SKILL.md) (how to raise debt findings in
  review), [react-next](../react-next/SKILL.md) and
  [fullstack-boundaries](../fullstack-boundaries/SKILL.md) (what "good shape"
  means in each layer)
- For debt whose repayment is an expensive-to-reverse decision:
  [architect/tradeoffs](../../../architect/skills/tradeoffs/SKILL.md)
