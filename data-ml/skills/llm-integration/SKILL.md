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
malformed, or down. Engineer accordingly: constrain the output at generation
when the API offers it (structured outputs, a schema the model must satisfy)
and validate it anyway before trusting it — an LLM promising JSON is not JSON
until parsed; handle timeouts and failures gracefully; and never let its raw
output reach a dangerous sink (a database, a shell, the DOM, a tool call)
unchecked. Everything the model READS is input from whoever wrote it — a
document, a ticket, a web page, a tool result — and instructions hidden in
that input are the attack ([security/threat-modeling](../../../security/skills/threat-modeling/SKILL.md)
maps it; [code-audit](../../../security/skills/code-audit/SKILL.md) hunts it).
Data is never promoted to instructions, whatever it says. "The model usually
returns the right format" is a production incident scheduled for later.

### 2. Prompts are code — versioned, reviewed, tested

A prompt is program logic expressed in English; treat it like source: in
version control (not pasted in a dashboard), reviewed, and changed
deliberately because a wording tweak can shift behavior across all users.
"Prompt engineering" by editing production text and eyeballing a few outputs is
how you ship a regression to everyone. Structure prompts for maintainability:
clear instructions, examples where they earn their place, and the current API's
recommended patterns (load the host's API reference skill for your provider,
if it exposes one — never from memory).

### 3. You cannot improve what you don't evaluate — build the eval set first

The single highest-leverage move in LLM work: a set of representative
inputs with known-good expected outputs (or graded criteria), so you can
measure a prompt/model change instead of vibing it. Without it, every "this
seems better" is [rung-1 evidence (`verification`)](../../../generalist/skills/verification/SKILL.md)
and you're tuning blind. Include the hard cases and the failure cases, not just
the happy demo, and size it to the regression you need to see: twenty cases
cannot show a five-percent drop. When the grader is itself an LLM, calibrate
it against human-labelled samples before its verdicts count — an uncalibrated
judge measures agreement with itself. This is [ml-modeling's](../ml-modeling/SKILL.md)
"you don't have a model until you can measure it" for LLMs — the eval set IS
the spec.

### 4. RAG: the answer is only as good as the retrieval

For retrieval-augmented generation, most quality problems are retrieval
problems, not generation problems: if the right context isn't retrieved, no
prompt saves the answer. Invest there first — chunking that preserves meaning,
embeddings suited to the domain, and measuring retrieval quality separately
(did we fetch the relevant docs?) from answer quality. Ground the model in
retrieved context and instruct it to say "I don't know" when the context
doesn't cover it — a confident hallucination is worse than an honest gap. Cite
sources so answers are verifiable. Choosing the lever: prompt first (cheapest
to change, easiest to measure); retrieval when the model lacks KNOWLEDGE it
can be given at request time; fine-tuning only for format, tone or a narrow
task at volume — never to teach it facts, which go stale the day after
training.

### 5. Cost and latency are design constraints from line one

Token cost and response time shape the architecture, not an afterthought:
choose the smallest model that clears the eval bar (not the biggest by
reflex), cache what repeats (identical/similar requests, and use prompt caching
for stable context), stream responses so latency is felt less, and set token
bounds so a runaway loop or hostile input can't autoscale your bill (the
[devops cost discipline (`infrastructure`)](../../../devops/skills/infrastructure/SKILL.md)
applied to tokens). Measure cost-per-request and latency percentiles like any
other production metric.

### 6. Workflow before agent — the model decides only where code can't

Most production "agents" are ordinary software with an LLM at the decision
points, and that is the correct shape, not a compromise. Climb the ladder only
as far as the task forces you: one call; then a **workflow** where code owns the
control flow and the model fills steps — a chain, a router, a fan-out with a
merge; then an orchestrator that splits work for workers when the subtasks
can't be listed in advance; and an autonomous loop last, only when the steps
genuinely cannot be predicted. Each rung up trades predictability, testability
and cost for flexibility you should be able to name. A while-loop the model
drives is the most expensive way to do something a `for` could.

### 7. An agent loop is bounded before it is smart

The moment the model can call tools and decide what to do next, the failure
mode stops being a wrong answer and becomes a wrong ACTION, repeated. Bound the
loop before tuning it:

- **Own the loop.** The `while` is yours, whatever framework you use: you
  decide when it retries, pauses and stops. A ceiling on turns and on spend
  ends the run with a report, not a crash, and "the model decides when it's
  finished" is not a stop condition — done, blocked and budget-spent are.
- **Keep each loop small and chain them by code.** A task that fits in a
  handful of steps stays coherent; one loop asked to do everything drifts.
  Several focused runs in a deterministic sequence beat one autonomous epic.
- **Least privilege on tools, and dedicated tools where it matters.** The agent
  gets the tools this task needs, not the ones the platform has. Anything that
  must be gated, audited or run in parallel becomes a dedicated tool with typed
  arguments — a `send_email` tool can be intercepted; a shell string that
  happens to send email cannot. Bash buys breadth; promote what needs control.
- **Approval is a tool the model calls, not a hope.** Before anything
  irreversible or outward-facing (send, pay, refund, delete, write outside the
  sandbox) the agent requests approval as a structured action that PAUSES the
  loop and shows the exact proposed operation — the recipient, the amount —
  never a summary of it. A human or a deterministic rule says yes.
- **State in, state out.** Each step takes the current state and returns the
  next one, with nothing living only in memory: that is what makes pause,
  resume, a human handoff and a replayed test trivial instead of impossible.
- **Failures and idempotency.** A tool error goes back to the model as
  information — reading an error and choosing a different move is the one
  self-correction that reliably works — and tools are idempotent, so a retry
  after a timeout doesn't refund twice.
- **Every tool result is untrusted input** (#1): content read on turn three
  can steer the tool call on turn four, which is why the allowlist and the
  gate exist at all. Filtering narrows the funnel; the gate closes it.
- **Long runs manage their context on purpose** — prune stale tool results,
  summarize when the window nears its limit, persist across sessions only what
  must survive — and **every call is telemetry**: prompt version, model id,
  tokens, cost, latency, tools invoked ([devops's `observability`](../../../devops/skills/observability/SKILL.md)
  applies), or the first incident is undebuggable.

### 8. Review is a separate call — the generator never grades itself

"Check your answer" inside the generating prompt is rung-1 evidence wearing a
gate's clothes: same context, same blind spots, same model agreeing with
itself. A verifier is a second call with a CLEAN context — the source and the
output, not the reasoning that produced it — or, better, a deterministic check
wherever one exists: a schema, a required field, a number that must match the
source, a test that runs. Add the verifier where the cost of a wrong output
is high (money, legal, medical, anything irreversible or user-facing at scale)
and skip it where a bad answer is cheap to spot and cheap to redo — a review
on every turn of a loop doubles cost for outputs nobody would have acted on.
Let the verifier feed back into another generation pass only when the
criteria are explicit and iteration measurably improves the result (the
evaluator-optimizer shape); without a measured gain it's two calls agreeing
to disagree at twice the price. When the verifier is an LLM judge, calibrate
it (#3) before trusting it; when the stakes are high enough, the verifier is a
person.

### 9. Design for the failure modes, because they're guaranteed

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
- The verifier idea, applied to code: [qa's `self-verification`
  discipline (`test-design`)](../../../qa/skills/test-design/SKILL.md) — an
  outsider finds what the author can't
- API facts (models, pricing, tool use, caching): the host's LLM-provider API
  reference skill if it exposes one — otherwise the provider's current docs,
  never memory. Output-as-attack-surface:
  [security/code-audit](../../../security/skills/code-audit/SKILL.md)
