---
name: ci-cd
description: >
  Build/test/deploy pipelines and release strategies: automation, stages,
  deployment patterns (blue-green, canary, rolling), and reversibility.
  Trigger: load when setting up or fixing CI/CD, choosing a deploy strategy, or
  when releases are painful, manual, or risky.
license: Apache-2.0
metadata:
  author: jrodrigopuca
  version: "1.0"
---

## When to Use

- Setting up or improving a build/test/deploy pipeline
- Choosing how to release (blue-green, canary, rolling, feature-flagged)
- Releases are manual, scary, slow, or occasionally broken
- "It works in CI but not in prod" (or the reverse)

## Critical Patterns

### 1. The pipeline is the single path to production — no side doors

Every change reaches prod the same way: commit → CI → deploy. No manual copies,
no "I'll just SSH in and fix it", no build-from-a-laptop. The moment there are
two ways to deploy, one of them is untested and it's the one that breaks. The
pipeline being the ONLY door is what makes prod reproducible and rollbackable.

### 2. Stages ordered by cost — fail fast, fail cheap

Order checks so the cheapest, most-likely-to-fail run first: lint/typecheck →
unit → integration → build → E2E → deploy. A developer waiting 20 minutes to
learn about a lint error stops trusting the pipeline. Fast feedback keeps the
pipeline a tool, not a toll booth. Cache aggressively (dependencies, layers,
build artifacts) — a slow pipeline gets bypassed, and a bypassed pipeline is a
side door (rule 1).

### 3. Build once, promote the same artifact

The artifact tested in staging is the EXACT artifact that goes to prod — same
bytes, promoted, not rebuilt. Rebuilding per environment means you deploy
something you never tested. Configuration changes per environment (injected at
deploy); the build does not. This is what makes "it passed staging" a real
guarantee instead of a hopeful one.

### 4. Pick the deploy strategy by blast-radius tolerance

| Strategy | How | Use when |
|----------|-----|----------|
| Rolling | Replace instances gradually | Default; stateless services, backward-compatible changes |
| Blue-green | Full parallel env, flip traffic | Need instant rollback, can afford double infra briefly |
| Canary | Route small % first, watch, expand | High-risk changes, enough traffic to get a signal fast |
| Feature flag | Ship dark, enable separately | Decouple deploy from release; per-cohort rollout |

The through-line: every strategy exists to SHRINK the blast radius of a bad
release and SHORTEN the time to undo it. Choose by how much a bad version can
hurt and how fast you'd need it gone.

### 5. Every deploy carries its rollback — decided before it ships

Before a release goes out, the answer to "how do we undo this in 2 minutes?"
must already exist: previous artifact kept warm, flag ready to flip, migration
reversible or forward-compatible. The dangerous case is database migrations:
never ship a migration and the code that requires it in one irreversible step —
use expand/contract (add column → deploy code using both → backfill → drop old)
so every intermediate state is rollback-safe. A deploy whose only recovery is
"roll forward a fix" is one bad Friday from an incident.

### 6. Green pipeline is sacred — a flaky build is a broken tool

A pipeline that fails randomly trains the team to hit "retry" and ignore red,
which is how a real failure ships. Treat pipeline flakiness like
[qa treats test flakiness (`test-design`)](../../../qa/skills/test-design/SKILL.md): quarantine
and fix within the week, never normalize. And a red main branch is a
stop-the-line event, not background noise — if main is broken, fixing it is the
team's top priority, because everyone builds on it.

## Resources

- Sibling skills: [observability](../observability/SKILL.md) (deploys need
  health signals to promote/rollback on), [infrastructure](../infrastructure/SKILL.md)
  (what the pipeline deploys onto)
- Reversibility doctrine: [stark/zero-to-one](../../../stark/skills/zero-to-one/SKILL.md);
  test discipline the pipeline enforces: [qa/test-design](../../../qa/skills/test-design/SKILL.md)
