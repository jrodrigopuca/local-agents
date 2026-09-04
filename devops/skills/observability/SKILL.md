---
name: observability
description: >
  Knowing what production is doing: logs, metrics, traces, meaningful alerts,
  and SLOs. Trigger: load when adding monitoring, designing alerts, debugging a
  production issue blind, or defining what "healthy" means for a service.
license: Apache-2.0
metadata:
  author: jrodrigopuca
  version: "1.1"
---

## Critical Patterns

### 1. Instrument with the feature, not after the outage

Observability is part of "done", same as tests and error states. A feature
shipped without the ability to answer "is it working in prod?" is a feature you
launched blind. The question to ask at build time: when this breaks at 3am,
what would I want to already be recorded? Add THAT now — after the outage, the
evidence you needed is gone.

### 2. The three signals, each answering a different question

- **Metrics** — "is something wrong, and how much?" Cheap, aggregate,
  always-on. The numbers you alert on and graph over time.
- **Logs** — "what exactly happened in this case?" Detailed, per-event.
  Structured (queryable fields, not string soup), with correlation IDs so one
  request is traceable across services.
- **Traces** — "where in the chain did the time/error go?" The request's path
  across services, the latency of each hop.

You need all three for different questions; reaching for logs to answer a
metrics question (grepping for "how often") is how you spend an outage doing
data entry.

### 3. Measure what users feel: the golden signals

Instrument the four that predict user pain: **latency** (how slow), **traffic**
(how much load), **errors** (how much is failing), **saturation** (how full —
CPU, memory, connections, queue depth). These generalize to almost any service
and map directly to "are users having a bad time?". Vanity metrics (total
requests served since launch) tell you nothing actionable — measure the RATE
and the DISTRIBUTION (p50/p95/p99, because the average hides the users in pain).

### 4. Alert on symptoms users feel, page on things humans must fix NOW

Two rules that kill alert fatigue:

- Alert on the SYMPTOM (error rate up, latency past SLO), not every possible
  cause — cause-alerts fire in dozens while the one symptom-alert tells you
  users are hurting.
- Every page must be **urgent, actionable, and real**: if the human can't or
  needn't do something right now, it's not a page — it's a dashboard or a
  ticket. A pager that cries wolf gets silenced, and then the real one is missed.

The test for any alert: "would I want to be woken up for this?" If no, demote it.

### 5. SLOs turn reliability into a decision instead of an argument

Define the Service Level Objective the users actually need (e.g. 99.9% of
requests succeed under 300ms over 30 days). It does two jobs: it's the
alerting threshold (page when you're about to miss it), and it's the **error
budget** (the 0.1% you're allowed to fail). Budget left → ship faster; budget
burning → stop feature work and harden. This replaces "is it reliable enough?"
opinion-fights with a number everyone agreed on in advance — same spirit as the
[architect's tradeoff flip-conditions (`tradeoffs`)](../../../architect/skills/tradeoffs/SKILL.md).

### 6. Dashboards tell a story, top-down

A good dashboard answers "are users okay?" at the top (the SLO/golden signals),
then drills into "if not, where?" below. A wall of 40 graphs with no hierarchy
is noise you'll ignore in the exact moment you need it. Build the dashboard you'd
want open DURING an incident — the [crisis-mode](../../../stark/skills/crisis-mode/SKILL.md)
triage (data loss? who's affected? spreading?) should be answerable from it in
seconds.

## Resources

- Sibling skills: [ci-cd](../ci-cd/SKILL.md) (deploys promote/rollback on these
  signals), [infrastructure](../infrastructure/SKILL.md) (what emits them)
- Where these signals get used under fire:
  [stark/crisis-mode](../../../stark/skills/crisis-mode/SKILL.md)
