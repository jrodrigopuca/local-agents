---
name: fullstack-boundaries
description: >
  Judgment for work that crosses the wire, in any stack: API contracts, runtime
  validation at edges, where logic lives, errors end-to-end. Trigger: load when
  work crosses the wire — designing/consuming APIs, handling forms, touching the
  data layer, or wiring frontend to backend.
license: Apache-2.0
metadata:
  author: jrodrigopuca
  version: "1.1"
---

## Critical Patterns

### 1. The wire is a trust boundary — validate everything that crosses it

A static type is a claim your compiler checked about your own code — it says
nothing about the bytes arriving from outside it. TypeScript erases types at
runtime, Python's hints are annotations, Java erases generics: in every case,
data crossing the wire is untyped until something at the edge proves otherwise.
Every entry point — request bodies, query params, form data, env vars, webhook
payloads, third-party API responses — gets a schema there. Parse, don't
validate-and-cast: the parser's output IS the interior type, so the check
happens once instead of defensively forever (Zod in TS, Pydantic in Python,
serde in Rust — same move, different spelling).

```
unknown → schema.parse() → typed domain value → interior code trusts it
```

One schema per contract, shared between producer and consumer when both are
yours (single source of truth for the type AND the validation).

### 2. Logic lives server-side by default

Business rules, authorization, price/total calculations, anything with
consequences: server. The client copy of a rule (e.g. form validation) is a UX
courtesy — a duplicate for fast feedback, never the enforcement. If the rule
exists ONLY in the client, it doesn't exist.

### 3. Design the contract before either side

Before implementing endpoint or component, write the contract: input schema,
output schema, and the error cases as part of the type — not as an afterthought.

- Errors are values in the contract (`{ ok: false, code: 'OUT_OF_STOCK' }`),
  distinguishable by the client without string-matching messages.
- Expected failures (validation, not-found, conflict) are modeled; exceptions
  are reserved for the genuinely exceptional.
- Never leak internals across the wire: stack traces, SQL errors, ORM entities.
  Map to the contract at the edge.

### 4. Errors travel end-to-end or they don't count

Trace every failure path to the pixel: DB error → mapped at the API edge →
typed error in the client → user sees something actionable (retry, fix input,
contact). A `500` that renders as an infinite spinner is an unfinished feature.
Same discipline for the boring states: loading, empty, and partial data are
states of the contract, not edge cases.

### 5. The database is not a dumping ground nor an oracle

- Constraints that must NEVER break (uniqueness, foreign keys, non-null) live in
  the database — application checks race, constraints don't.
- Queries stay close to the data: filter/aggregate in SQL, not by loading rows
  into JS and looping. N+1s are found by looking at query logs, not by vibes.
- Migrations are code: reviewed, reversible where possible, never hand-run.

### 6. Secrets and authz are edge concerns, checked every time

- Secrets exist only server-side; anything prefixed for client exposure
  (`NEXT_PUBLIC_*`) is public by definition — treat it as such.
- Authorization is checked where the data is served (the API/action), not where
  the button is hidden. UI gating is UX; server gating is security.

## Resources

- Schema patterns: a `zod-4` skill; strict typing: a `typescript` skill — load
  either if the host exposes it (both ship outside this catalog; otherwise use
  the library's current docs)
- Sibling skill: [react-next](../react-next/SKILL.md) — the client side of these
  contracts
- For expensive contract decisions (versioning, sync vs async):
  [architect/tradeoffs](../../../architect/skills/tradeoffs/SKILL.md)
