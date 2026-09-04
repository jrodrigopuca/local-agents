---
name: code-review
description: >
  Reviewing Swift/SwiftUI code as mentor: the severity system, the
  Apple-specific defect checklist, and review-as-teaching. Trigger: load when
  the user shares Swift, SwiftUI, UIKit, or AppKit code for review, feedback,
  or "is this okay?".
license: Apache-2.0
metadata:
  author: jrodrigopuca
  version: "1.1"
---

_Verified against Xcode 26 / iOS 26 / macOS 26 (September 2026). Apple moves
these facts yearly — if the year has changed, re-check a claim before teaching it._

## Critical Patterns

### 1. Review in three passes, report by severity

Pass 1 — **correctness & safety** (🔴): retain cycles, force unwraps, data
races, main-thread violations, leaked resources. Pass 2 — **design** (🟡):
logic in views, missing abstractions, state ownership, testability. Pass 3 —
**style** (🟢): naming, idiom, formatting. Report blockers first; never bury
a retain cycle under twelve naming nits. Every finding carries its failure
case ("this closure captures self strongly; when X outlives Y, the whole
graph leaks") — and when the code is genuinely good, say WHAT is good with
the same precision.

### 2. The Swift-specific 🔴 checklist

- **Retain cycles**: `self` captured strongly in escaping closures stored by
  `self` (handlers, subscriptions, timers); delegates declared strong. A
  bare `Task { }` retains `self` only until it finishes — that is not a
  cycle; the leak needs BOTH `self` storing the task AND the task never
  completing (an endless `for await`). `[weak self]` sprinkled on every Task
  is cargo cult: prove the ownership graph, and cancel stored tasks on scope
  exit instead.
- **Force unwraps** (`!`, `try!`, `as!`): each one is a crash with a date TBD.
  Acceptable only with a written invariant ("IBOutlet after viewDidLoad") —
  otherwise `guard let` with a real fallback path.
- **Concurrency**: UI state touched off the main actor; shared mutable state
  without actor/lock protection; `Task` fire-and-forget hiding errors;
  blocking calls inside actors. In Swift 6 language mode, isolation and
  Sendable violations are compile errors; blocking inside an actor and
  fire-and-forget Tasks are NOT — the compiler is an ally for the first two
  only. And under Xcode 26's MainActor default with caller-actor async, the
  new 🔴 runs the other way: heavy work silently on main because nobody
  marked it `@concurrent` (see [state-architecture #6](../state-architecture/SKILL.md)).
- **Error swallowing**: `try?` discarding errors the user needs to see;
  empty catch blocks — an error that vanishes silently becomes QA's
  [flow-hunting](../../../qa/skills/flow-hunting/SKILL.md) finding later.

### 3. The SwiftUI 🟡 checklist

- **Logic in the view**: formatting, filtering, network calls inline in
  `body` → belongs in the ViewModel/model; `body` is a pure function of
  state, and every recomputation runs it.
- **State ownership**: `@State` for view-local only; one source of truth per
  piece of state — two views each "owning" a copy is the bug factory;
  `@Binding` down, not state duplicated down.
- **Observation hygiene**: with `@Observable`, a view re-evaluates only when
  a property its `body` READ changes — so "re-renders on unrelated changes"
  is the `ObservableObject`/`@Published` smell (any published change
  invalidates every observer), and `ObservableObject` in new code is the
  finding. For `@Observable` models the finding is a `body` that reads far
  more than it shows: narrow what `body` touches or split into subviews
  (diffing works per view).
- **SwiftData**: `ModelContext` or `@Model` objects crossing actors 🔴 (not
  Sendable); `@Query` inside a ViewModel 🟡 (view-only, main-actor);
  relationships without delete rules 🟡; a schema change in a shipped app
  without a `VersionedSchema` + migration plan 🔴 — that is a crash on
  upgrade, not on first install.
- **Untested-by-omission** 🟡: a ViewModel behind a protocol-fronted service
  with no Swift Testing target is testability that never cashed in; and a
  `@MainActor` ViewModel's tests are `@MainActor`/awaited or they don't
  compile in Swift 6.
- **The missing states**: view renders happy path only — where are loading,
  empty, error? (The screen-state enum from
  [state-architecture](../state-architecture/SKILL.md), and the ux-ui
  [five states (`ux-flows`)](../../../ux-ui/skills/ux-flows/SKILL.md) — same table.)

### 4. Platform-honesty: iOS code isn't Mac code automatically

When the target includes macOS: check window/scene assumptions (Mac has many
windows, resizable), keyboard/menu/right-click support, `NavigationSplitView`
over stack navigation for wide layouts, sandbox entitlements for file access.
Flag "iOS-shaped" code shipped to Mac as 🟡 — it runs, and it feels like a
port, which Mac users smell instantly.

### 5. Review as teaching: pattern over instance

The user's growth beats the diff. When the same mistake appears three times,
teach the PATTERN once (with the underlying rule: "closures that outlive the
call need an ownership decision") instead of flagging three instances — then
have them find the third occurrence themselves. One concept per review
(mentorship contract #7); the rest goes to pending topics.

## Resources

- Sibling skills: [state-architecture](../state-architecture/SKILL.md) (where
  the design findings point), [debugging](../debugging/SKILL.md) (when a
  finding needs a repro)
- Generic review altitude and severity honesty:
  [senior-dev/pairing](../../../senior-dev/skills/pairing/SKILL.md),
  [architect/design-review](../../../architect/skills/design-review/SKILL.md)
