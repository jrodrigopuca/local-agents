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
  version: "1.0"
---

## When to Use

- Writing up findings from an audit into something the dev can act on
- Prioritizing a backlog of security issues
- Prescribing the fix (and the systemic control behind it)
- Verifying that a fix actually closed the hole

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

Use a real scale (CVSS-ish, or critical/high/medium/low), and calibrate:
unauthenticated + remote + high-impact + easy = drop everything; theoretical +
deep behind other controls + low-impact = backlog. Inflating everything to
critical trains the team to ignore you (the boy who cried RCE); underplaying a
real hole to be agreeable ships a breach. Report the honest severity, recommend
the order, and let the team own the schedule — same split as
[qa's severity-vs-priority](../../../qa/skills/bug-reporting/SKILL.md).

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
class into a solved problem — the security version of
[code-health's](../../../senior-dev/skills/code-health/SKILL.md) "fix the
class, not the instance".

### 4. Fixes go through the dev — you prescribe, they implement

Same boundary as [qa](../../../qa/AGENTS.md): you find, demonstrate, and
prescribe; the developer who owns the code implements the fix (they carry the
context to do it without breaking behavior). You can write the exact fix in
the report and pair on it — but the merge is theirs. Route architectural fixes
(a whole auth redesign) to [architect](../../../architect/AGENTS.md); functional
fallout to [senior-dev](../../../senior-dev/AGENTS.md).

### 5. Verify like a security fix, not a feature fix

A patch that stops YOUR specific PoC may not close the hole — attackers don't
stick to your payload. Verification: re-run the original PoC (must fail), then
try the variations (different encoding, different parameter, the bypass around
the specific check), then confirm the CLASS control actually covers the
siblings the audit found. And add the regression test — a security test that
would have caught it, living where [qa/test-design](../../../qa/skills/test-design/SKILL.md)
says. A fix verified only against the exact PoC is a fix on layaway.

### 6. Handle the report itself securely

The findings ARE sensitive — a live-vuln list is an attacker's shopping list.
Share it with the people who fix it, through channels that won't leak it; don't
paste real exploits or real secrets into public issues/PRs; if a secret leaked,
rotation happens BEFORE the writeup circulates (the writeup names that it
leaked, not the value). For anything reaching real users, coordinate disclosure
timing with the fix — public detail before the patch is landed is handing out
the weapon ([ethics rules](../../AGENTS.md)).

## Resources

- Sibling skills: [threat-modeling](../threat-modeling/SKILL.md),
  [code-audit](../code-audit/SKILL.md) (the source of what's being remediated)
- Report/verify discipline shared with QA:
  [qa/bug-reporting](../../../qa/skills/bug-reporting/SKILL.md); evidence bar:
  [generalist/verification](../../../generalist/skills/verification/SKILL.md)
