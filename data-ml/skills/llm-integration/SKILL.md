---
name: llm-integration
description: >
  Building reliable product features on LLMs: RAG, prompting-as-code, output
  validation, evals, and cost/latency engineering. Trigger: load when
  integrating an LLM into a product — chat, extraction, RAG, agents, or any
  "add AI to this" request.
license: Apache-2.0
metadata:
  author: jrodrigopuca
  version: "1.1"
---

## Critical Patterns

### 1. Treat the LLM as an unreliable external dependency

It's a network call to a probabilistic service that can be slow, wrong,
malformed, or down. Engineer accordingly: validate its output against a schema
before trusting it (an LLM promising JSON is not JSON until parsed), handle
timeouts and failures gracefully, and never let its raw output reach a
dangerous sink (a DB, a shell, `dangerouslySetInnerHTML`) unchecked — that's
[security/code-audit](../../../security/skills/code-audit/SKILL.md) territory,
prompt injection is real. "The model usually returns the right format" is a
production incident scheduled for later.

### 2. Prompts are code — versioned, reviewed, tested

A prompt is program logic expressed in English; treat it like source: in
version control (not pasted in a dashboard), reviewed, and changed
deliberately because a wording tweak can shift behavior across all users.
"Prompt engineering" by editing production text and eyeballing a few outputs is
how you ship a regression to everyone. Structure prompts for maintainability:
clear instructions, examples where they earn their place, and the current API's
recommended patterns (load the user's claude-api reference for those).

### 3. You cannot improve what you don't evaluate — build the eval set first

The single highest-leverage move in LLM work: a set of representative
inputs with known-good expected outputs (or graded criteria), so you can
measure a prompt/model change instead of vibing it. Without it, every "this
seems better" is [rung-1 evidence (`verification`)](../../../generalist/skills/verification/SKILL.md)
and you're tuning blind. Include the hard cases and the failure cases, not just
the happy demo. This is [ml-modeling's](../ml-modeling/SKILL.md) "you don't
have a model until you can measure it" for LLMs — the eval set IS the spec.

### 4. RAG: the answer is only as good as the retrieval

For retrieval-augmented generation, most quality problems are retrieval
problems, not generation problems: if the right context isn't retrieved, no
prompt saves the answer. Invest there first — chunking that preserves meaning,
embeddings suited to the domain, and measuring retrieval quality separately
(did we fetch the relevant docs?) from answer quality. Ground the model in
retrieved context and instruct it to say "I don't know" when the context
doesn't cover it — a confident hallucination is worse than an honest gap. Cite
sources so answers are verifiable.

### 5. Cost and latency are design constraints from line one

Token cost and response time shape the architecture, not an afterthought:
choose the smallest model that clears the eval bar (not the biggest by
reflex), cache what repeats (identical/similar requests, and use prompt caching
for stable context), stream responses so latency is felt less, and set token
bounds so a runaway loop or hostile input can't autoscale your bill (the
[devops cost discipline (`infrastructure`)](../../../devops/skills/infrastructure/SKILL.md)
applied to tokens). Measure cost-per-request and latency percentiles like any
other production metric.

### 6. Design for the failure modes, because they're guaranteed

LLMs hallucinate, drift between model versions, and behave non-deterministically.
Engineer around it: keep humans in the loop where the cost of a wrong answer is
high, show confidence/sources so users can judge, pin model versions and
re-run your eval set before adopting a new one (a model upgrade is a change to
test, not a free improvement), and give users a path when the AI is wrong. The
[gamification honesty test (`engagement`)](../../../gamification/skills/engagement/SKILL.md)
applies: would the user, seeing how this works, trust it — or feel deceived by
a confident machine that was guessing?

## Resources

- Sibling skills: [ml-modeling](../ml-modeling/SKILL.md) (eval discipline),
  [data-pipelines](../data-pipelines/SKILL.md) (RAG data needs the same quality bar)
- API facts (models, pricing, tool use, caching): the host's LLM-provider API
  reference skill if it exposes one — otherwise the provider's current docs,
  never memory. Output-as-attack-surface:
  [security/code-audit](../../../security/skills/code-audit/SKILL.md)
