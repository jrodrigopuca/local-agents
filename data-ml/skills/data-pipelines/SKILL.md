---
name: data-pipelines
description: >
  Moving data reliably: ingestion, transformation, quality validation, storage,
  and pipeline design. Trigger: load when building or fixing data pipelines,
  ETL/ELT, data quality issues, or deciding how to store and model data.
license: Apache-2.0
metadata:
  author: jrodrigopuca
  version: "1.1"
---

## When to Use

- Building ingestion / transformation / ETL / ELT pipelines
- Data quality problems (bad values, gaps, silent corruption)
- Deciding storage: warehouse, lake, database, format
- A downstream model or report is getting wrong numbers

## Critical Patterns

### 1. Understand the data before you move it

Before writing a pipeline, profile the source: what each field actually means
(not what its name suggests), its ranges, its nulls, its duplicates, its
encoding, how it's generated and how often it lies. Most pipeline bugs are
misunderstandings of the source dressed up as code bugs — the "amount" column
that's sometimes cents and sometimes dollars, the timestamp in three timezones,
the "unique" id that isn't. Curiosity here is cheaper than debugging downstream.

### 2. Validate at the boundary — data contracts, not hope

Every pipeline stage that ingests data checks it against an explicit contract:
expected schema, types, ranges, nullability, referential integrity. Bad data is
caught and quarantined at the door, not discovered three tables downstream as a
wrong dashboard number. This is [fullstack-boundaries](../../../senior-dev/skills/fullstack-boundaries/SKILL.md)
applied to data: the source is untrusted until validated, and a silent bad row
is worse than a loud rejected one because it poisons everything computed from it.

### 3. Idempotent and reprocessable — run it twice, same result

Pipelines fail and get re-run; a stage that double-counts on re-run or corrupts
on partial failure is a data-integrity time bomb. Design each stage to be
idempotent (re-running produces the same state, not duplicates) and able to
reprocess a date range without manual surgery. When a bug ships in the
transform logic, you WILL need to reprocess history — build for that day from
the start.

### 4. Prefer ELT and keep the raw layer immutable

Land raw source data untouched first (immutable, append-only), then transform
into cleaned/modeled layers on top. Two payoffs: when transform logic has a bug
(it will), you reprocess from raw instead of re-fetching from a source that may
have changed; and the raw layer is your audit trail of what actually arrived.
Transforming-on-ingest and discarding the original throws away your only ground
truth.

### 5. Model storage for how it's read, name it for humans

Choose storage by access pattern: OLTP database for transactional app reads,
columnar warehouse for analytics/aggregation, object storage for big/raw/blobs.
Don't run analytics queries against the production OLTP database — you'll hurt
the app and the query. Model the analytical layer for the questions asked
(star-ish schemas, sensible grain) and name tables/columns so an analyst
understands them without a decoder ring — undocumented cryptic schemas are where
data trust goes to die.

### 6. Observe data like you observe services

Data pipelines fail silently in a way services don't: they keep running and
produce wrong numbers. Add data-specific monitoring — freshness (did today's
data arrive?), volume (row count in expected range, not suddenly half?),
distribution (did a key metric's shape shift?), and null/duplicate rates.
This is [observability](../../../devops/skills/observability/SKILL.md) for
data: the alert you want is "the numbers look wrong" BEFORE a stakeholder sees
the wrong number in a report.

## Resources

- Sibling skills: [ml-modeling](../ml-modeling/SKILL.md) (the consumer of clean
  data — garbage in, garbage out starts here), [llm-integration](../llm-integration/SKILL.md)
  (retrieval data needs the same rigor)
- Boundary/observability discipline: [senior-dev/fullstack-boundaries](../../../senior-dev/skills/fullstack-boundaries/SKILL.md),
  [devops/observability](../../../devops/skills/observability/SKILL.md)
