---
name: data-modeling
description: >
  Designing schemas that survive real data: entities, keys, constraints,
  normalization and when to break it, and modelling access alongside structure.
  Trigger: load when designing a new schema, reviewing a proposed table or ORM
  model, or when an existing model keeps producing awkward queries.
license: Apache-2.0
metadata:
  author: jrodrigopuca
  version: "1.1"
---

## When to Use

- A feature needs new persisted state (a table, a collection, a document shape)
- Reviewing someone's proposed schema or ORM model before it ships
- Queries keep coming out awkward, or the same data lives in three places
- Deciding what is a column, what is a row, and what is its own table

## Critical Patterns

### 1. Model the questions, not just the nouns

Entities tell you what exists; the queries tell you what the model has to make
cheap. Before drawing tables, write down the handful of questions the system
will ask constantly — "the last 20 orders for this user, newest first", "every
unpaid invoice past due" — because those determine keys, sort order, and which
columns need to live together. A model designed from the entity diagram alone
is a model whose access paths are an accident.

### 2. Constraints are documentation the database enforces

A foreign key says "this cannot point at nothing" in a way that survives a
migration script, a second service, and a manual fix at 2am. NOT NULL, UNIQUE
and CHECK say what is true about the domain — and unlike a comment or a
validation in one codebase, they stay true. Push every rule you can into the
schema: what you leave in application code only holds while that code is the
only writer, which is never permanently true.

### 3. Normalize until it hurts, denormalize until it works

Start normalized: one fact in one place, so an update is one write and cannot
leave the database disagreeing with itself. Then denormalize deliberately,
where measurement shows the join is the problem — and when you do, write down
what now keeps the copies in sync and what happens when that fails. Duplicated
data is not a sin; duplicated data with nobody owning its consistency is.

### 4. Choose keys for what they promise, not for habit

A primary key is an identity claim: it must be unique, never change, and never
be reused. Natural keys carry meaning but change more often than people expect
(emails, usernames, tax IDs). Surrogate keys are stable but say nothing, so
the natural uniqueness still needs its own constraint next to them — otherwise
you've made duplicates possible and merely hidden them behind different IDs.
Sequential versus random matters too: sequential keys leak volume and order,
random ones scatter writes across the index.

### 5. Nullable is a modelling decision, not a default

Every nullable column is a question the model refuses to answer: does NULL mean
unknown, not-applicable, or not-yet? Three meanings in one value produce three
different bugs. Often the honest fix is structural — a separate table for the
optional relationship, or a status column that names the states explicitly —
rather than a column that is sometimes absent for reasons nobody wrote down.

### 6. Time is data, and "current" is a projection

Rows that only ever hold the latest value silently destroy history: you cannot
answer "what did this look like when the order shipped" from a table that only
knows now. Decide deliberately whether a fact is current-only, versioned, or
append-only — and store timestamps with their timezone semantics stated, not
assumed. Retrofitting history onto a mutable table means the answer for
everything before today is gone.

## Resources

- Sibling skills: [migrations](../migrations/SKILL.md) (changing this model
  once it holds real rows), [query-performance](../query-performance/SKILL.md)
  (the access paths this model implies)
- Where the wire meets the store:
  [senior-dev's `fullstack-boundaries`](../../../senior-dev/skills/fullstack-boundaries/SKILL.md);
  boundary and ownership questions:
  [architect's `design-review`](../../../architect/skills/design-review/SKILL.md)
- Analytical modelling of derived data (star schemas, grain) is a different
  craft: [data-ml's `data-pipelines`](../../../data-ml/skills/data-pipelines/SKILL.md)
