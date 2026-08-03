---
name: infrastructure
description: >
  Infrastructure as code, containers, environments, cloud, secrets, and
  scaling: building reproducible systems from zero. Trigger: load when
  provisioning infra, containerizing, managing environments/secrets, or making
  scaling/cost decisions.
license: Apache-2.0
metadata:
  author: jrodrigopuca
  version: "1.0"
---

## When to Use

- Provisioning or changing cloud infrastructure
- Containerizing an app or designing environments
- Managing secrets, config, or environment parity
- Scaling, capacity, or cloud-cost decisions

## Critical Patterns

### 1. Infrastructure as code — the repo IS the source of truth

Every piece of infra is declared in version-controlled code (Terraform,
Pulumi, CloudFormation, whatever), reviewed like application code, and applied
through the pipeline. Two consequences that matter: prod can be rebuilt from
zero without anyone's memory, and every change has a diff, an author, and a
rollback. The click-ops server configured by hand in a console is the thing
that takes the whole team down and nobody can say why — because there's no
record of what it was.

### 2. No snowflakes — environments are cattle, not pets

Servers/containers are identical, disposable, and replaceable, not lovingly
hand-maintained individuals. If fixing a sick instance means logging in to
nurse it, the design is wrong — kill it and let automation bring up a fresh
one. Immutable infrastructure (rebuild-and-replace over modify-in-place) makes
"what state is this box in?" a question with a known answer: the one the code
declares.

### 3. Dev/prod parity — shrink the "works on my machine" gap

The closer dev, staging, and prod are, the fewer surprises ship. Same OS, same
runtime versions, same dependencies (containers make this cheap); differences
live ONLY in injected config, never in code paths or versions. The gaps that
remain (prod has real scale, real data volume, real network latency) are named
explicitly so nobody mistakes "passed staging" for "will work at 10x load".

### 4. Config in the environment, secrets in a manager — never in the repo

Config that varies per environment is injected at runtime (env vars, config
service), not baked into the build (per [ci-cd](../ci-cd/SKILL.md) "build once").
Secrets — tokens, keys, DB passwords — live in a secrets manager (Vault, cloud
KMS/Secrets Manager), never committed, never in plain env files in the repo,
never in logs. A leaked secret is rotated immediately (this is where
[security](../../../security/AGENTS.md) and you overlap). `NEXT_PUBLIC_*` and
friends are public by definition — treat anything client-shipped as already
disclosed.

### 5. Least privilege everywhere, by default

Every service, pipeline, and human gets the minimum access to do its job —
scoped IAM roles, narrow security groups, no shared god-credentials. The reason
is blast radius ([devops judgment #7](../../AGENTS.md)): when something IS
compromised (and assume it will be), least privilege is what stops one foothold
from becoming total. Over-broad permissions are the quiet default that turns a
small breach into a headline.

### 6. Scale and cost are the same conversation, measured not guessed

Scale for the load you HAVE plus headroom, not the load you fantasize about —
premature autoscaling across regions for traffic that isn't scheduled is the
[architect's imaginary-scale hedging (`tradeoffs`)](../../../architect/skills/tradeoffs/SKILL.md)
with a cloud bill. Prefer scaling that's automatic and bounded (max limits, so
a bug or attack can't autoscale you into bankruptcy). Watch spend as a metric
with alerts, not as a monthly surprise: the bill is an architecture decision,
and the biggest line item usually reveals a design choice worth revisiting.

## Resources

- Sibling skills: [ci-cd](../ci-cd/SKILL.md) (deploys onto this),
  [observability](../observability/SKILL.md) (watches it)
- Overlaps: [security/code-audit](../../../security/skills/code-audit/SKILL.md)
  (config/secrets as attack surface),
  [architect/tradeoffs](../../../architect/skills/tradeoffs/SKILL.md) (infra is
  full of one-way doors)
