---
name: migrations
description: >
  Changing a schema that already holds real data: expand/contract, reversible
  steps, backfills that don't lock, and stating what a deploy strategy must
  respect. Trigger: load when altering an existing table, renaming or dropping
  anything, backfilling data, or when a release couples code to a schema change.
license: Apache-2.0
metadata:
  author: jrodrigopuca
  version: "1.1"
---

## Critical Patterns

### 1. Expand, migrate, contract — never rename in place

The rename is the trap: it makes old code and new code mutually exclusive, so
there is a moment where one of them is broken no matter the deploy order.
Instead: **expand** (add the new column/table, nothing reads it yet),
**migrate** (write to both, backfill the old rows), **switch** (reads move to
the new shape), **contract** (stop writing the old, then drop it — in a later
release). Each step is deployable alone and revertible alone. The sequence is
slower and it is the only version that can be undone on a Friday.

### 2. A migration coupled to a deploy is a rollback you cannot do

If rolling back the code requires rolling back the schema, you have no rollback
— restoring a schema means restoring data written since. Schema changes go out
BEFORE the code that needs them and stay backward-compatible with the currently
running version. That constraint is not negotiable by release pressure; it is
what makes the release reversible at all, and
[devops's `ci-cd`](../../../devops/skills/ci-cd/SKILL.md) is designing the
rollout around it.

### 3. Backfills are batched, resumable, and observable

Updating ten million rows in one statement takes a lock, blows the transaction
log, and leaves you with nothing if it fails at 90%. Batch it, commit per
batch, record progress so it can resume, and rate-limit it so production
traffic keeps its resources. Run it as a separate operation from the schema
change — a backfill inside a migration turns a five-second deploy into an
outage of unknown length.

### 4. Know which operations take which lock, on YOUR engine

"Adding a column is cheap" is true on some engines, for some column types, in
some versions — and catastrophic in the others, because a default value
rewrites every row while holding an exclusive lock. This is the one place where
engine specifics dominate the judgment: check what your engine and version
actually do for that operation at your table size, and say the answer in lock
duration, not in adjectives.

### 5. Migrations are code — reviewed, versioned, and tested against real shape

They belong in version control, run in order, and execute exactly once. Test
them against a dataset with production-like volume and skew: a migration
verified only against an empty dev database has been verified against the one
case that never occurs. And write the down path, or state explicitly that there
isn't one — an irreversible migration is a decision worth making consciously,
not a detail discovered during an incident.

### 6. Destructive steps wait, and they wait longer than feels necessary

Dropping the old column right after the switch feels tidy and removes your
escape route. Let the contract phase lag by a full release cycle at minimum:
long enough that a rollback to the previous version still finds what it needs,
and long enough that a bug in the new path can be fixed by pointing back rather
than by restoring from backup.

## Resources

- Sibling skills: [data-modeling](../data-modeling/SKILL.md) (the shape you are
  moving toward), [query-performance](../query-performance/SKILL.md) (index
  builds are migrations with their own locking story)
- Rollout, windows and rollback mechanics:
  [devops's `ci-cd`](../../../devops/skills/ci-cd/SKILL.md); proving the
  migration ran correctly before claiming it did:
  [generalist's `verification`](../../../generalist/skills/verification/SKILL.md)
