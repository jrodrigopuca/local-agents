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

## When to Use

- Deciding whether/how to apply ML to a problem
- Choosing a model, training, or improving one
- Designing how to evaluate a model honestly
- Putting a model into production and keeping it healthy

## Critical Patterns

### 1. Frame the problem before touching a model

Translate the business need into an ML problem precisely: what's predicted
(the target), from what (features available AT PREDICTION TIME — not features
that only exist after the fact, the classic leakage trap), what a right/wrong
answer costs, and what "good enough to ship" means as a number. A fuzzy framing
produces a model that scores well and helps nobody. Sometimes the honest output
of framing is "this doesn't need ML" — a rule or a query wins; say so.

### 2. Baseline first — it's the yardstick, not the warm-up

Build the dumbest reasonable predictor first: most-frequent-class, a simple
rule, a linear model. It sets the bar every fancier model must beat to justify
its cost, and it's frequently good enough to ship while the "real" model is
still training. A deep model that barely beats predicting-the-average is a
complex liability; you only know that because you measured the baseline.

### 3. Split honestly, or your metrics are fiction

Train / validation / test, with the test set touched only at the end. The
cardinal sins that inflate every metric: **leakage** (information from the
future or the target sneaking into features), **train/test contamination**
(the same rows or near-duplicates in both), and **temporal leakage** (random
splits on time-series, so you "predict" the past from the future). For
time-based problems, split by time. A 99% accuracy is far more often leakage
than genius — suspect it, hunt it.

### 4. Measure what the decision costs, not what's convenient

Accuracy is the wrong metric for most real problems (99% accuracy on a 1%-fraud
dataset means you caught zero fraud). Pick the metric that matches the cost
structure: precision/recall/F1 when classes are imbalanced or errors are
asymmetric, calibration when you need trustworthy probabilities, the actual
business metric (dollars, hours saved) when you can. And always look at
performance PER SLICE — a model that's great overall and terrible for one user
group is a fairness incident waiting to ship ([judgment #7](../../AGENTS.md)).

### 5. A model in production is a system, not an artifact

Deployment is where models rot: the world drifts and the model doesn't. Ship
with — monitoring of input distributions (is production data still like
training data?) and output/quality metrics, a defined retraining trigger, and
a fallback for when the model is unsure or unavailable (degrade gracefully, per
[devops](../../../devops/AGENTS.md) reliability thinking). "Deployed" is the
start of the model's maintenance, not the finish line — [verification](../../../generalist/skills/verification/SKILL.md)
here means watching real predictions, not the offline test score.

### 6. Reproducibility and explainability are features

Track every experiment: data version + code version + params → metrics, so
"the good run" is reproducible and comparisons are real
([data-pipelines](../data-pipelines/SKILL.md) rigor for models). And prefer a
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
