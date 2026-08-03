---
name: shipping
description: >
  Getting apps into users' hands: signing, provisioning, TestFlight, App
  Review, and macOS-specific distribution (notarization, outside-MAS).
  Trigger: load on anything involving certificates, provisioning profiles,
  TestFlight, App Store Connect, App Review, entitlements, or distributing a
  Mac app.
license: Apache-2.0
metadata:
  author: jrodrigopuca
  version: "1.0"
---

## When to Use

- Code signing / provisioning errors (the classic time-eaters)
- Preparing a TestFlight build or an App Store submission
- App Review questions, rejections, or metadata work
- Distributing a macOS app — inside OR outside the Mac App Store

## Critical Patterns

### 1. This is the no-Socratic zone — answer first, demystify second

Signing pain teaches nothing ([mentorship ladder](../../AGENTS.md), exception
c): give the fix immediately, THEN the one mental model that makes the whole
area stop being magic: **a signed app = your code + entitlements (what it may
do) + a certificate (who you are) + a provisioning profile (the notarized
permission slip binding cert + app ID + capabilities + devices)**. Ninety
percent of signing errors are one of those four disagreeing with the others —
read the error asking "WHICH pair disagrees?" and let Xcode's automatic
signing do its job unless there's a concrete reason for manual.

### 2. TestFlight is a release rehearsal, not a formality

The build that goes to TestFlight is release-configured: optimizations on,
debug flags off, real (or realistic) backend — bugs that only exist in
release builds (timing, optimization, missing debug scaffolding) are found
HERE or by users. Internal testers = instant, external = brief review. Ship
with meaningful "what to test" notes and working feedback collection; a beta
nobody can give feedback on is theater. Every release candidate walks the
core flows on a REAL DEVICE before submission — simulator-only confidence is
rung-2 evidence.

### 3. App Review: read the rejection as a spec, not an insult

Prevent the classics before submitting: every permission string
(`NSCameraUsageDescription`...) says WHY in user terms; demo account provided
if login gates content; no placeholder screens; privacy labels matching what
the app actually collects; payments through IAP when the rules say so.
On rejection: it cites a guideline number — read THAT guideline, respond to
THAT point (fix or a factual appeal). Arguing with the general unfairness of
Apple is a hobby, not a strategy. Budget review time into every deadline
(days, not hours) — telling stakeholders "it's done" when review hasn't
started is a false "done" per the
[verification bar](../../../generalist/skills/verification/SKILL.md).

### 4. macOS is a different distribution planet — decide the channel first

The channel decision shapes the build, so it comes first:

| Channel | Requires | Buys you | Costs you |
|---------|----------|----------|-----------|
| Mac App Store | Sandbox + MAS review | Discovery, trusted install, IAP | Sandbox limits, review cycle |
| Direct (site/GitHub) | Developer ID signing + **notarization** + hardened runtime | Full power, instant releases, own pricing | Your own updater (Sparkle), payments, no store discovery |

Notarization is non-negotiable for direct distribution — an unnotarized app
greets users with a scary Gatekeeper block, which is a first impression that
[ux-ui](../../../ux-ui/AGENTS.md) would classify as a broken empty state for
your whole product. Automate it in CI (`notarytool`) so it's a step, not an
event.

### 5. Entitlements and sandbox: request the minimum, explain every ask

Each entitlement/permission is user trust spent. Sandbox file access beyond
user-selected files, network server, camera — request only what the feature
in front of the user justifies, at the MOMENT it's justified (permission
prompts at first launch, before any value delivered, are the
[gamification's `flow-analysis`](../../../gamification/skills/flow-analysis/SKILL.md)
"premature ask" anti-pattern with an OS dialog). On macOS, test the sandboxed
build specifically — code that worked unsandboxed and dies sandboxed is a
classic day-before-release surprise.

### 6. Releases are versioned, automated, and reversible-ish

Build numbers increment monotonically (automate — rejected-for-duplicate-build
is a self-inflicted wound); version bumps follow semver-ish user expectations;
release notes written for users, not commit logs. Phased release ON for
anything risky (halt-able mid-rollout — the closest the App Store gets to the
[stark parachute (`zero-to-one`)](../../../stark/skills/zero-to-one/SKILL.md) doctrine), and
a rollback story thought through BEFORE shipping: you can't pull a build
back, only ship a fix forward — so the fix-forward path (hotfix branch,
expedited review request) is part of the release plan, not an improvisation.

## Resources

- Sibling skills: [code-review](../code-review/SKILL.md) (release-readiness
  findings), [debugging](../debugging/SKILL.md) (release-build-only bugs)
- Crisis handling when a bad build ships:
  [stark/crisis-mode](../../../stark/skills/crisis-mode/SKILL.md)
