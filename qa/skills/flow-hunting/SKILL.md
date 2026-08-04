---
name: flow-hunting
description: >
  Systematic hunting of unconsidered paths: edge cases, interruptions, state
  collisions, and hostile inputs. Trigger: load when exploring a feature or
  flow for potential bugs, reviewing a spec for gaps, or asked "what could
  break here?".
license: Apache-2.0
metadata:
  author: jrodrigopuca
  version: "1.1"
---

## When to Use

- A feature is "done" and needs adversarial eyes before shipping
- Reviewing a spec/design for the paths it doesn't mention
- A production bug appeared and the question is "what else like this exists?"
- Writing the test plan for anything non-trivial

## Critical Patterns

### 1. Walk the flow three times, as three different people

First as the INTENDED user (does the happy path even deliver?). Then as the
CONFUSED user (wrong order, back button, double submit, abandons midway and
returns tomorrow). Then as the HOSTILE user (crafted input, URL editing,
expired tokens, no permissions). Most teams only ever walk it the first way —
walks two and three are where your findings live.

### 2. The interruption sweep — every flow, every step

At EACH step of a flow, ask what happens on: browser back / forward / refresh,
tab close and return via link, session expiry mid-flow, network drop mid-save,
double-click on submit, opening the same flow in two tabs, deep-linking
straight into the middle. Interruptions are the most under-designed dimension
of flows because no spec ever mentions them — which is exactly why you check
every one.

### 3. Boundary torture for every input

For each input (field, list, file, parameter), probe the edges mechanically:
empty / whitespace-only, minimum, minimum−1, maximum, maximum+1, zero, one,
negative, decimal where int expected, emoji + unicode + RTL text, HTML/script
fragments, absurdly long, duplicate of existing, leading/trailing spaces. For
collections: 0 items, 1 item, exactly-page-size, thousands. Boundaries are
where off-by-ones live, and off-by-ones are the most common bug in software.

### 4. State × action collision grid

List the entity's states (draft, active, archived, deleted, expired...) and
every action (edit, share, pay, cancel...). The grid's cells nobody specified
are your hunting ground: what DOES happen when you edit an archived item via a
stale tab? When payment succeeds for an order cancelled in parallel? Race the
transitions: act during loading, cancel during saving. Every unspecified cell
is either a bug or a missing spec line — both are findings.

### 5. Trust boundaries get extra suspicion

Wherever data crosses a boundary (user input, API response, file upload, URL
params, webhooks — the same map as
[fullstack-boundaries](../../../senior-dev/skills/fullstack-boundaries/SKILL.md)),
test the crossing: what if it's malformed, missing fields, the wrong type,
stale, replayed? And the authorization cut: take every URL/action from a
privileged session and replay it as an unprivileged one — UI hiding a button
is not the same as the server refusing the action.

### 6. Timebox, charter, report the coverage honestly

Exploration without structure becomes wandering. Work in charters: "explore
[area] with [heuristic] to find [risk class]" — 30-60 minutes each,
prioritized by risk (impact × likelihood × recency of change). Close each
charter with: paths covered, findings, and — critically — paths NOT covered.
The uncovered list is what makes "QA looked at it" an honest sentence
([judgment #3-4](../../AGENTS.md)).

## Resources

- Sibling skills: [test-design](../test-design/SKILL.md) (turning found paths
  into permanent checks), [bug-reporting](../bug-reporting/SKILL.md) (filing
  what the hunt catches)
- The five UI states demanded at design time:
  [ux-ui/ux-flows](../../../ux-ui/skills/ux-flows/SKILL.md)
