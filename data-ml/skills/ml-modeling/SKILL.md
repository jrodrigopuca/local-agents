---
name: ml-modeling
description: >
  Framing and building ML solutions honestly: problem framing, baselines,
  evaluation, and deployment. Trigger: load when framing an ML problem,
  choosing/training a model, designing evaluation, or deploying a model to
  production.
license: Apache-2.0
metadata:
  author: jrodrigopuca
  version: "1.1"
---

## Critical Patterns

### 1. Frame the problem before touching a model

Translate the business need into an ML problem precisely: what's predicted
(the target), from what (features available AT PREDICTION TIME — not features
that only exist after the fact, the classic leakage trap), what a right/wrong
answer costs, and what "good enough to ship" means as a number — written down
BEFORE training, because it is also the stop rule: past that number, another
week of tuning is spend without a decision behind it. Labels are data too:
who produced them, how often two labelers agree, and what a label costs decide
the ceiling of everything trained on them. A fuzzy framing produces a model
that scores well and helps nobody. Sometimes the honest output of framing is
"this doesn't need ML" — a rule or a query wins; say so.

### 2. Baseline first — it's the yardstick, not the warm-up

Judgment #3 as a step: most-frequent-class, a simple rule, a linear model,
before anything else. It sets the bar every fancier model must beat to justify
its cost, and it is frequently good enough to ship while the "real" model is
still training.

### 3. Split honestly, or your metrics are fiction

Train / validation / test, with the test set touched only at the end. The
cardinal sins that inflate every metric: **leakage** (information from the
future or the target sneaking into features), **train/test contamination**
(the same rows or near-duplicates in both), and **temporal leakage** (random
splits on time-series, so you "predict" the past from the future). For
time-based problems, split by time. A 99% accuracy is far more often leakage
than genius — suspect it, hunt it.

### 4. Measure what the decision costs, not what's convenient

Judgment #4 chose the metric's shape; this chooses the metric: precision,
recall or F1 when classes are imbalanced or errors are asymmetric, calibration
when you need trustworthy probabilities, the actual business metric (dollars,
hours saved) when you can. Always per SLICE — a model that's great overall and
terrible for one user group is a fairness incident waiting to ship
([judgment #7](../../AGENTS.md)). And the offline score is not the finish
line: the loop closes only when the DECISION the model serves (judgment #1) is
measured in production — a holdout or an A/B against the baseline — because a
model can improve its metric and change nothing the business cares about.

### 5. A model in production is a system, not an artifact

Deployment is where models rot: the world drifts and the model doesn't — and
before drift, there is training-serving skew: a feature computed one way in
the notebook and another way in the request path, so the model in production
never saw the data it was trained on. Compute features once, from one
definition, for both. Ship with monitoring of input distributions (is
production data still like training data?) and output/quality metrics, a
defined retraining trigger, and a fallback for when the model is unsure or
unavailable (degrade gracefully, per [devops](../../../devops/AGENTS.md)
reliability thinking). "Deployed" is the
start of the model's maintenance, not the finish line — [verification](../../../generalist/skills/verification/SKILL.md)
here means watching real predictions, not the offline test score.

### 6. Reproducibility and explainability are features

Judgment #5 in practice: data version + code version + params → metrics for
every run, so "the good run" is reproducible and comparisons are real. And prefer a
model whose decisions you can explain when the stakes require it — a slightly
less accurate model you can defend to a user, a regulator, or a debugging
session often beats a black box you can't. When ML makes a decision about a
person, "the model said so" is not an acceptable explanation.

## Resources

- Sibling skills: [data-pipelines](../data-pipelines/SKILL.md) (clean data is
  the precondition), [llm-integration](../llm-integration/SKILL.md) (when the
  "model" is a foundation model)
- Complexity-justification and deployment reliability:
  [architect/tradeoffs](../../../architect/skills/tradeoffs/SKILL.md),
  [devops/observability](../../../devops/skills/observability/SKILL.md)
