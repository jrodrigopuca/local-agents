---
name: query-performance
description: >
  Making reads cheap by design: execution plans, index strategy, N+1 detection,
  and diagnosing slowness against real cardinality instead of guessing.
  Trigger: load when a query or page is slow, when designing the access paths a
  feature needs, or when deciding whether an index is worth its cost.
license: Apache-2.0
metadata:
  author: jrodrigopuca
  version: "1.1"
---

## When to Use

- Something got slow, especially "it was fine until we had real data"
- Designing which indexes a new feature's queries require
- Deciding whether to add an index, or whether an existing one earns its keep
- An ORM is emitting queries nobody wrote and nobody has read

## Critical Patterns

### 1. Read the plan before touching anything

The execution plan is the only source of truth about what the database actually
does — everything else is a theory. Get it with real parameters against
production-like volume, and read it for three things: what it scans, what it
sorts, and where the row estimate diverges from reality. A plan whose estimate
says 12 rows where 400,000 arrive explains the slowness by itself, and no index
added on a hunch will fix a query you haven't looked at. This is the
[evidence ladder](../../../generalist/skills/verification/SKILL.md) applied to
performance: measured, not assumed.

### 2. Indexes are a write tax paid for a read discount

Every index makes writes slower and consumes space; it earns that by turning a
scan into a lookup. So the question is never "would an index help this query"
but "does this query matter enough to tax every insert on the table". Index the
access paths the product actually depends on, drop the ones nothing uses, and
know that an unused index is pure cost with no benefit — invisible until you
look for it.

### 3. Composite index order is decided by the predicate, not by taste

A multi-column index serves queries that filter its columns left to right:
`(user_id, created_at)` answers "this user's rows, newest first" and also
"this user's rows", but not "everything since Tuesday". Order equality columns
before range columns, and include the sort column so the sort disappears
instead of happening afterwards. Getting the order wrong produces an index that
exists, looks reassuring, and is never used.

### 4. N+1 is a model problem wearing a code costume

One query for the list plus one per row is the most common performance bug in
any ORM-backed application, and it never appears in development where the list
has four items. Find them in the query log, not by reading application code —
the emitted SQL is the truth, and the ORM call that produced it looks perfectly
innocent. The fix is stating the access path (eager load, explicit join,
batched fetch), which is why this lands here rather than staying with
[senior-dev](../../../senior-dev/AGENTS.md): the code is where it surfaces, the
model is where it lives.

### 5. Selectivity decides whether an index can help at all

An index on a column with three distinct values across a million rows cannot
save you: the database will correctly decide that scanning is cheaper than
following pointers for a third of the table. Know the cardinality before
prescribing — and when a low-selectivity filter really must be fast, the answer
is usually structural (a partial index, a different partitioning of the data),
not another index on the same column.

### 6. Fix the class, not the query

A single slow endpoint patched with one index is a symptom treated. Ask what
made it possible: a missing convention about pagination, an ORM default that
loads everything, a table that grew a dimension nobody modelled. The systemic
answer — a query budget in review, a lint against unbounded fetches, a
different shape — is what stops the next five. Same instinct as
[security's `remediation`](../../../security/skills/remediation/SKILL.md)
prescribing against the vulnerability class instead of the instance.

## Resources

- Sibling skills: [data-modeling](../data-modeling/SKILL.md) (access paths
  belong to the model), [migrations](../migrations/SKILL.md) (building an index
  on a live table is itself a migration)
- When slowness is above the database — payload size, waterfalls, render cost —
  it belongs to
  [senior-dev's `fullstack-boundaries`](../../../senior-dev/skills/fullstack-boundaries/SKILL.md);
  when it is about the system around it, to
  [devops's `observability`](../../../devops/skills/observability/SKILL.md)
