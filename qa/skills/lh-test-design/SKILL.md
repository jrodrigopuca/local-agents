---
name: lh-test-design
description: >
  Judgment for writing and reviewing test code: what to test at which level,
  how to keep tests trustworthy, and how to audit an existing suite. Trigger:
  load when writing test code, reviewing a test suite, or deciding what
  automated coverage a feature needs.
license: Apache-2.0
metadata:
  author: jrodrigopuca
  version: "1.1"
  local-agents-id: "sk-66f4fd"
---

## Critical Patterns

### 1. Test at the lowest level that can catch the bug

The pyramid is an economics argument, not a dogma: unit tests are cheap,
fast, and precise; E2E tests are expensive, slow, and vague about causes. Push
each check DOWN: pure logic → unit; component contracts and DB queries →
integration; and E2E only for the few journeys where the money is (login,
checkout, the core loop) — testing through the UI what a unit test could catch
is paying E2E prices for unit information. Inverted pyramids (everything E2E)
fail slowly, flake often, and explain nothing.

### 2. Test behavior at the contract, not implementation guts

A test that breaks when the code is refactored (behavior unchanged) is
friction; a test that survives a bug is dead weight. Aim at the CONTRACT:
given these inputs/state, this output/effect. Don't assert internal call
sequences or private state — mock at boundaries you don't own (network, clock,
randomness), keep real code running everywhere else. The question for every
test: "if this fails, does it mean a USER-visible promise broke?"

### 3. Every test tells one story: arrange, act, assert

One behavior per test, named as the behavior ("rejects expired coupon at
checkout", not "test3"). Failure output must diagnose without a debugger:
assert specific values, not just truthiness. Shared fixtures for the boring
setup, but the MEANINGFUL data visible in the test itself — a test whose
critical input hides in a factory five files away can't be read as a story.

### 4. Deterministic, or quarantined with an owner — the flakiness rule

A test that fails sometimes is worse than no test: it trains the team to
retry-until-green, which buries real failures. Flakiness causes are almost
always: real time (`sleep`, timeouts) → use fake clocks and explicit waits on
conditions; shared state between tests → isolate per test; network to real
services → stub the boundary; ordering assumptions → make each test
self-contained. Quarantine a flaky test the day it flakes, with an owner and
a date, and fix it that week — a quarantine that lasts a quarter is a
graveyard. Delete it only when the behaviour it guards is covered elsewhere:
a deleted test on a critical path is a coverage hole that shows up green. And
a check that is stochastic by nature — a model's output, a latency — is not
flaky: assert a threshold over N samples, never a single run.

### 5. Coverage guides, contracts decide

Line coverage finds UNtested code (useful); it never proves tested code is
well-tested (a test with no meaningful asserts covers 100% and checks
nothing). Audit a suite by asking: are the RISKS covered — the boundaries from
[lh-flow-hunting](../lh-flow-hunting/SKILL.md), the state collisions, the auth cuts?
Ten tests on the tricky boundary beat a hundred on getters. Never chase a
coverage number for its own sake; it optimizes exactly the wrong behavior.

### 6. Work inside the dev's conventions — you're a guest in the suite

Test code is code: it follows the repo's existing patterns, naming, helpers,
and framework idioms (read the neighboring tests first, per the senior-dev's
"read before write"). If the suite's conventions are actively harmful (shared
mutable fixtures, sleeps everywhere), don't silently fork your own style —
raise it with the dev as a finding, agree the pattern, then apply it. For
framework specifics, load a `playwright` / `pytest` skill if the host exposes one.

## Resources

- Sibling skills: [lh-flow-hunting](../lh-flow-hunting/SKILL.md) (the paths worth
  automating), [lh-bug-reporting](../lh-bug-reporting/SKILL.md) (every confirmed bug
  ends as a regression test here)
- The dev's testing philosophy this composes with:
  [senior-dev](../../../senior-dev/AGENTS.md), Developer Judgment #5 (tests
  as a safety net, not a ceremony — the numbered list under that heading, not
  the Peer Contract's)
