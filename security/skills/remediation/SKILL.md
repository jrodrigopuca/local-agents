---
name: remediation
description: >
  Turning security findings into fixes: the actionable report, severity
  ranking, fix-the-class prescriptions, and verification. Trigger: load when
  reporting vulnerabilities, prioritizing a findings list, prescribing fixes,
  or verifying a security fix.
license: Apache-2.0
metadata:
  author: jrodrigopuca
  version: "1.1"
---

## Critical Patterns

### 1. The finding is only done when the dev can fix it

A security report that says "SQL injection in the user module" wasted
everyone's time. Every finding carries, in dev terms:

1. **What** — the vulnerability class and the exact location (file, line, endpoint)
2. **Attack** — what an attacker DOES with it, concretely (the minimal PoC / the
   request), so severity is self-evident and the dev believes it
3. **Impact** — what it costs when exploited (whose data, how much, how far)
4. **Fix** — the specific remediation, in code terms, not "sanitize input"
5. **Class control** — the systemic change that prevents the whole category

The WHY is not optional garnish — a dev who understands what the attacker does
fixes it correctly and doesn't reintroduce it next sprint. That's the
communication mandate: dev-level, detailed, always the reason.

### 2. Rank by exploitability × impact — and be honest both directions

Judgment #4 as a report: use a real scale (CVSS-ish, or
critical/high/medium/low) and calibrate — unauthenticated + remote +
high-impact + easy = drop everything; theoretical + deep behind other controls
+ low-impact = backlog. Severity is yours, the schedule is the team's; that
split, and why inflating burns trust, is
[qa's severity-vs-priority (`bug-reporting`)](../../../qa/skills/bug-reporting/SKILL.md)
and is not restated here. Two outcomes a report must allow for: **accept the
risk** — a won't-fix is a decision with a named signer and a compensating
control, written into the report, never a silent backlog entry; and **fix
later, mitigate now** — a fix that is months away ships with a mitigation
today (a rule at the edge, the feature behind a flag, the endpoint rate-limited),
because the timeline is part of the remediation, not a footnote to it.

### 3. Prescribe the safe-by-default fix, not the whack-a-mole patch

The best remediation makes the vulnerability class impossible to reintroduce,
not just gone from this line:

| Instead of | Prescribe |
|------------|-----------|
| Escaping this one query | Parameterized queries everywhere; ban string-built SQL (lint) |
| Adding an authz check here | A default-deny authorization layer every handler passes through |
| Fixing this XSS | Framework auto-escaping on; a single sanitizer for the rare raw-HTML case |
| Removing this committed secret | Secret scanning in CI + rotation + a secrets manager (and rotate the leaked one NOW) |

Point-fixes leave the other instances live; safe-by-default converts the whole
class into a solved problem — judgment #6 ("fix the class, not just the
instance") turned into a prescription, and the same instinct as
[code-health's](../../../senior-dev/skills/code-health/SKILL.md) rule of
three: the third occurrence is a pattern, not a coincidence.

### 4. Fixes go through the dev — you prescribe, they implement

The [qa](../../../qa/AGENTS.md) boundary, applied here: you find, demonstrate
and prescribe, down to the exact fix in the report; the developer who owns the
code merges it. Architectural fixes (a whole auth redesign) go to
[architect](../../../architect/AGENTS.md); functional fallout to
[senior-dev](../../../senior-dev/AGENTS.md).

### 5. Verify like a security fix, not a feature fix

A patch that stops YOUR specific PoC may not close the hole — attackers don't
stick to your payload. Verification: re-run the original PoC (must fail), then
try the variations (different encoding, different parameter, the bypass around
the specific check), then confirm the CLASS control actually covers the
siblings the audit found. And add the regression test — a security test that
would have caught it, living where [qa/test-design](../../../qa/skills/test-design/SKILL.md)
says. A fix verified only against the exact PoC is a fix on layaway.

### 6. Handle the report itself securely

The persona's ethics rule ("handle findings responsibly") binds; what it
doesn't spell out: if a secret leaked, rotation happens BEFORE the writeup
circulates, and the writeup names that it leaked, not the value; and for
anything reaching real users, the disclosure has a clock — the fix lands, then
the detail is published, and the gap between them is agreed with whoever
operates the system, in days, before the report is shared beyond the people
fixing it.

## Resources

- Sibling skills: [threat-modeling](../threat-modeling/SKILL.md),
  [code-audit](../code-audit/SKILL.md) (the source of what's being remediated)
- Report/verify discipline shared with QA:
  [qa/bug-reporting](../../../qa/skills/bug-reporting/SKILL.md); evidence bar:
  [generalist/verification](../../../generalist/skills/verification/SKILL.md)
