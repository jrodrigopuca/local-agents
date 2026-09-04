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
  version: "1.1"
---

_Verified against Xcode 26 / iOS 26 / macOS 26 (September 2026). Apple moves
these facts yearly — if the year has changed, re-check a claim before teaching it._

## Critical Patterns

### 1. This is the no-Socratic zone — answer first, demystify second

Signing pain teaches nothing ([mentorship ladder](../../AGENTS.md), exception
c): give the fix immediately, THEN the one mental model that makes the whole
area stop being magic: **a signed app = your code + entitlements (what it may
do) + a certificate (who you are) + a provisioning profile (the Apple-SIGNED
permission slip binding cert + app ID + capabilities + devices)**. Not
"notarized": notarization is a separate, macOS-only step (#4), and using one
word for both is the most common confusion in this whole area. Ninety
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
rung-2 evidence. TestFlight builds expire after 90 days; a beta that nobody
rebuilt in three months is a beta nobody can install.

### 3. App Review: read the rejection as a spec, not an insult

Prevent the classics before submitting: every permission string
(`NSCameraUsageDescription`...) says WHY in user terms; demo account provided
if login gates content; no placeholder screens; privacy labels matching what
the app actually collects; a `PrivacyInfo.xcprivacy` declaring required-reason
APIs and tracking domains (enforced since May 2024 — ITMS-91053 is the missing
one, and third-party SDKs on Apple's list need their own); the age-rating
questionnaire in its 2025 form (4+/9+/13+/16+/18+ — since February 2026
updates are blocked until it's answered). Payments: IAP by default, but
external purchase links and alternative marketplaces now exist per region (EU
under the DMA, US after the 2025 Epic ruling) — verify the rule for YOUR
storefront, it changes by court and by year.
On rejection: it cites a guideline number — read THAT guideline, respond to
THAT point (fix or a factual appeal). Arguing with the general unfairness of
Apple is a hobby, not a strategy. Budget review time into every deadline
(days, not hours) — telling stakeholders "it's done" when review hasn't
started is a false "done" per the
[verification bar](../../../generalist/skills/verification/SKILL.md).

### 4. macOS is a different distribution planet — decide the channel first

iOS has channels too (App Store, TestFlight, enterprise/custom apps via Apple
Business Manager, EU alternative marketplaces and web distribution), but they
share one build. On macOS the channel changes the BUILD, so the decision
comes first:

| Channel | Requires | Buys you | Costs you |
|---------|----------|----------|-----------|
| Mac App Store | Sandbox + MAS review | Discovery, trusted install, IAP | Sandbox limits, review cycle |
| Direct (site/GitHub) | Developer ID signing + **notarization** + hardened runtime | Full power, instant releases, own pricing | Your own updater (Sparkle), payments, no store discovery |

Notarization is non-negotiable for direct distribution — an unnotarized app
greets users with a scary Gatekeeper block, which is a first impression that
[ux-ui](../../../ux-ui/AGENTS.md) would classify as a broken empty state for
your whole product. Since macOS 15 the Control-click "Open" bypass is gone:
an unnotarized app sends the user to System Settings > Privacy & Security,
which is a support ticket, not a workaround. Automate it in CI —
`notarytool submit --wait`, then `stapler staple` — so it's a step, not an
event; without the staple, first launch needs an online check.

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
Certificates expire on their own clock (Developer ID in years, distribution
sooner): shipped apps keep launching, new builds stop signing — the renewal
date lives in the calendar, not in release week.

## Resources

- Sibling skills: [code-review](../code-review/SKILL.md) (release-readiness
  findings), [debugging](../debugging/SKILL.md) (release-build-only bugs)
- Crisis handling when a bad build ships:
  [stark/crisis-mode](../../../stark/skills/crisis-mode/SKILL.md)
