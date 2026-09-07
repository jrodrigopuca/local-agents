---
name: tradeoffs
description: >
  Method for analyzing and presenting expensive-to-reverse technical decisions:
  drivers, options, tradeoff table, recommendation, ADR shape. Trigger: load when
  a decision is costly to change later (data model, service boundaries, framework,
  sync/async, build-vs-buy), when the user asks "should we use X or Y", or when
  a project decision needs recording or an existing one is being reopened.
license: Apache-2.0
metadata:
  author: jrodrigopuca
  version: "1.1"
---

## Critical Patterns

### 1. Reversibility check first

Before any analysis: **how expensive is this to undo?** If it's cheap (rename,
internal refactor, swappable lib behind an interface), say so, give a fast
recommendation, and don't burn the user's time on ceremony. Full analysis is for
one-way doors.

### 2. Drivers before options

Extract the real drivers before comparing anything. Ask (or infer from context)
in this order:

1. **Scale & load** — actual numbers, not aspirations ("we'll be huge" is not a driver)
2. **Team** — size, seniority, what they already operate well
3. **Rate of change** — which parts of the system change weekly vs yearly
4. **Consistency & failure tolerance** — what breaks, and who cares, when it's stale or down
5. **Data shape** — when an option splits, copies or reshapes persisted data,
   its cost is a cardinality, a lock window or a lost constraint, not an
   adjective; that number comes from [dba](../../../dba/AGENTS.md), and an
   option priced without it is priced wrong
6. **Deadline & budget reality**

A comparison without drivers produces the generic blog-post answer. The drivers
ARE the analysis; the table is just its display.

### 3. The tradeoff table — 2 or 3 options, never 1, rarely 5

Always include the boring option (status quo / simplest thing) as a real
candidate, not a strawman. For each option, state cost in terms of the DRIVERS,
not generic pros/cons:

```
| Option | Driver it serves | What it costs | Reversal cost |
```

If every row of "what it costs" is empty or vague, you don't understand the
options yet — go investigate before presenting.

### 4. Recommend. Always.

Presenting a table without a pick is delegating your job upward. State a
recommendation, the driver that decides it, and the condition that would flip it
("I'd pick Postgres here; if the write volume actually reaches X, revisit").
The flip condition is what makes a recommendation honest instead of dogmatic.

### 5. Capture as a lightweight ADR

For decisions that clear the reversibility bar, leave a written trace:

```markdown
# ADR-{n}: {decision in one sentence}
- Status: accepted | superseded by ADR-{m}
- Drivers: {the 2-3 that actually decided it}
- Decision: {what we're doing}
- Tradeoff accepted: {what this costs us, stated plainly}
- Revisit if: {the flip condition}
```

Five lines beat a wiki page nobody updates. The "revisit if" line is the most
valuable one — it converts future arguments into a lookup.

**Where it lives, how it is consulted, when it is superseded.** The record
goes in the repo, next to the code it constrains: the project's existing
decision log if it has one, otherwise `docs/adr/NNNN-slug.md`, one decision
per file, numbered so the order of thinking survives, with a `README.md` in
the folder that holds one line per decision — number, title, status. The
folder name is the signal: any developer or agent who sees `adr/` knows what
it is without being told. Drivers carry the NUMBER that decided it (a million
rows, page 400 taking seconds), not the meeting it came from, because the
meeting is what nobody remembers in six months; "Revisit if" is a condition
someone can check ("the product needs jump-to-page N"), never a date, because
a date can't be evaluated against the code. Anchor the decision to real paths
where it applies. A record is read on the way to a decision, not on the way
back from a mistake: before anything that clears the reversibility bar, open
the index and cite what is already decided — an accepted ADR is applied and
its "Revisit if" checked, not re-derived from scratch and not overturned in
silence — and the repo's own instructions file (`AGENTS.md`, or whatever the
host reads at startup) should point at the folder so the read happens without
anyone remembering to ask. An accepted
record is never edited: when the DECISION changes, a new one says
`Supersedes: ADR-n` and the old one's status flips to `superseded by ADR-m`,
so the chain of why is preserved; a changed implementation detail under the
same decision is not a new record — that inflation is how logs die. Nothing
here crosses projects: a decision that shows up in two repos is a skill
candidate, not an index entry.

### 6. Anti-patterns to name when you see them

- **Resume-driven design** — the driver is the tech, not the problem
- **Premature distribution** — microservices/queues before a monolith hurts
- **Imaginary-scale hedging** — paying today for load that isn't scheduled
- **Pattern maximalism** — hexagonal + CQRS + event sourcing on a CRUD app

Call them out warmly, with the cost they'd incur — never with mockery.

## Resources

- Sibling skill: [design-review](../design-review/SKILL.md) — evaluates the
  system these decisions produced
- Inherited: [generalist verification](../../../generalist/skills/verification/SKILL.md)
  — claims about "X scales better" follow the evidence ladder too
