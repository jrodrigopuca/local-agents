---
name: code-audit
description: >
  Exhaustive code auditing for vulnerability classes: injection, authz, auth,
  secrets, crypto, deps, and the method for reading code adversarially.
  Trigger: load when auditing code for security flaws, reviewing a diff for
  vulnerabilities, or hunting a specific vuln class.
license: Apache-2.0
metadata:
  author: jrodrigopuca
  version: "1.0"
---

## When to Use

- Auditing a codebase, module, or diff for security vulnerabilities
- Following up a [threat-modeling](../threat-modeling/SKILL.md) suspicion
- Verifying whether a specific vuln class is present

## Critical Patterns

### 1. Read like an attacker: follow tainted data, not the control flow

Don't read the code the way it runs — read the way data ENTERS and chase it.
Trace every input from its source (the door) to its sinks (query, command,
HTML, filesystem, response). A vulnerability is tainted data reaching a
dangerous sink without a sanitizing gate in between. `rg` the sinks first
(query builders, `exec`, `dangerouslySetInnerHTML`, `eval`, file ops,
deserializers), then walk backwards to see if attacker-controlled data can
reach them.

### 2. The high-yield vulnerability classes (audit in this order of ROI)

| Class | The question | Where it hides |
|-------|--------------|----------------|
| Broken authorization (IDOR/authz) | Can user A act on user B's object? | Endpoints that take an ID and skip the "is it YOURS?" check |
| Injection (SQL/NoSQL/cmd/LDAP) | Does input reach an interpreter unparameterized? | String-built queries, shelled-out commands, dynamic eval |
| Broken authentication | Can I skip/forge/replay the identity check? | Token validation, session fixation, weak reset flows, missing rate limits |
| Secrets exposure | What's committed, logged, or shipped to the client? | Repos, env in errors, `NEXT_PUBLIC_*`, verbose logs, source maps |
| XSS / output injection | Does untrusted data render unescaped? | Templates bypassing auto-escape, `innerHTML`, unsanitized markdown |
| Insecure deserialization / SSRF / XXE | Does the app fetch/parse attacker input? | URL fetchers, XML parsers, object deserializers |
| Sensitive-data / crypto misuse | Rolled-own crypto, weak hashing, data at rest | Custom "encryption", `md5(password)`, plaintext PII |

Authorization is #1 by ROI on purpose — it's the most common serious flaw and
the least caught by scanners, because it requires understanding INTENT (whose
data is this?), which only a human/agent reading the logic can judge.

### 3. Authorization gets checked at every object access, every time

The single highest-value audit habit: for each endpoint/action that touches a
specific record, verify the code confirms the CURRENT user may touch THAT
record — not just that they're logged in (authentication ≠ authorization), not
that the UI hid the button (client gating ≠ enforcement). Multi-tenant systems:
every query must be scoped to the tenant, and "must" means you check each one.
An `/api/invoice/{id}` that returns any id to any authenticated caller is the
most common serious bug in web software.

### 4. Validate at boundaries — read for the MISSING gate

At each trust boundary from the [threat model](../threat-modeling/SKILL.md),
the audit looks for the check that ISN'T there: input reaching logic without a
schema parse, an ID used without an ownership check, a redirect using an
unvalidated URL, a file path built from user input (traversal), a limit that
isn't enforced (mass assignment writing fields the user shouldn't set). The
vulnerability is an absence — train the eye to notice the guard that should be
present and isn't, which is harder than spotting a wrong line.

### 5. Dependencies and config are attack surface too

Audit isn't only your code: check dependency versions against known CVEs,
lockfile integrity, and over-permissioned packages (their code runs as yours).
Config is code: default credentials, debug mode in prod, permissive CORS,
missing security headers, over-broad IAM/DB grants, exposed admin interfaces,
verbose error pages leaking stack traces. The boring misconfiguration ships
more breaches than the clever exploit.

### 6. Confirm before you claim — PoC to the minimum, honesty about the rest

A suspected vuln is rung-2 until demonstrated. Where safe and authorized,
prove it minimally (the request returning another user's record — not the
script dumping the whole table, per the
[ethics rules](../../AGENTS.md)). Where you can't safely confirm, report it as
"suspected, unconfirmed" with the reasoning — never dress a hypothesis as a
confirmed hole ([evidence ladder](../../../generalist/skills/verification/SKILL.md)).
And record what you audited AND what you didn't: a clean audit of five
endpoints says nothing about the sixth.

## Resources

- Sibling skills: [threat-modeling](../threat-modeling/SKILL.md) (aims the
  audit), [remediation](../remediation/SKILL.md) (turns findings into fixes)
- Functional-defect cousin: [qa/flow-hunting](../../../qa/skills/flow-hunting/SKILL.md);
  the boundary discipline being read adversarially:
  [senior-dev/fullstack-boundaries](../../../senior-dev/skills/fullstack-boundaries/SKILL.md)
