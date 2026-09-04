---
name: state-architecture
description: >
  SwiftUI state management and app architecture: ownership, MVVM shape,
  navigation, dependency injection, project structure. Trigger: load on
  questions about state ("why doesn't my view update?"), architecture, where
  code should live, or how to structure a new feature/project.
license: Apache-2.0
metadata:
  author: jrodrigopuca
  version: "1.1"
---

_Verified against Xcode 26 / iOS 26 / macOS 26 (September 2026). Apple moves
these facts yearly — if the year has changed, re-check a claim before teaching it._

## Critical Patterns

### 1. Every piece of state has exactly one owner — find it first

The diagnostic question for 90% of SwiftUI confusion: **who owns this state?**
One source of truth; everyone else gets a reference (`@Binding`, a passed
value, an observed model). Symptoms of violated ownership: two copies that
drift, `onChange` chains syncing state to state, views that "sometimes"
update. The fix is never a cleverer sync — it's deleting the second copy.

### 2. The ownership ladder (SwiftUI edition)

Place state at the lowest rung that satisfies it — same logic as the
senior-dev's [state placement ladder (`react-next`)](../../../senior-dev/skills/react-next/SKILL.md),
different vocabulary:

```
1. Derived      — computed property; don't store what you can compute
2. @State       — owned HERE: transient value state (toggle, text, sheet
                  visibility) AND the view's own @Observable model —
                  `@State private var vm = ViewModel()` is how a view owns
                  a ViewModel under Observation (it replaced @StateObject)
3. @Binding     — owned above, mutated here; @Bindable when the owner is an
                  @Observable object and you need `$`
4. Passed model — an @Observable owned by a parent, read here with no wrapper
                  at all (that is @ObservedObject's replacement)
5. Environment  — cross-cutting reads (theme, session):
                  `@Environment(Session.self)` for @Observable objects —
                  injection, not a junk drawer
6. App-level    — one composition root owning shared services/models
```

A view creating a model a parent already owns (rung 2 where rung 4 was
right), and Environment used as a global variable, are the two chronic
misplacements. Reaching for `@StateObject`/`@ObservedObject` in new code is
the third: they are the pre-Observation API and teach the old update model.

### 3. MVVM, the honest version

- **View**: declares UI as a function of state; forwards intent
  (`vm.didTapSave()`); computes nothing business-y.
- **ViewModel** (`@Observable`, `@MainActor`): screen state as an enum
  (`loading / loaded(Data) / empty / error(Error)` — keep the `Error`, a
  `String` is a screenshot of a failure; make illegal combinations
  unrepresentable, per the senior-dev's types-as-design rule), intent
  methods, zero `import SwiftUI`.
- **Services**: protocol-fronted (`protocol InvoiceRepository`), injected by
  init, async APIs. The protocol is what makes the ViewModel testable with a
  fake — that's dependency injection earning rent, not ceremony.
- **SwiftData in this shape**: `@Query` is a View-layer read — main-actor,
  view-only — so it never lives in a ViewModel. Simple list screens use
  `@Query` in the view and skip the VM; screens with logic put a
  `ModelContext` behind a repository protocol the VM is injected with;
  background imports run in a `@ModelActor` and hand back Sendable
  snapshots, because `@Model` objects and `ModelContext` do not cross actors.
- Anti-pattern to name when seen: ViewModels that are just pass-throughs to
  services with no state to manage (not every view needs one) — and god
  ViewModels owning three screens' state (split by screen).

### 4. Navigation is state too

Model navigation as data: `NavigationStack(path:)` with typed destinations,
sheets/alerts driven by optional state (`item:`), not by imperative calls
scattered through views. Deep linking then becomes "set the state" instead of
a special subsystem. On macOS/iPad, `NavigationSplitView` is the default
shape — design navigation state so the same model renders stack-on-iPhone,
split-on-wide (platform honesty from
[code-review #4](../code-review/SKILL.md)).

### 5. Project structure screams features, not types

`Features/Invoices/ (View, ViewModel, models)`, `Services/`, `Shared/` —
grouping by feature keeps change local (the architect's
[screaming architecture (`design-review`)](../../../architect/skills/design-review/SKILL.md)
applied to Xcode). Folders named `Views/`, `ViewModels/`, `Models/` with
thirty files each is structure by species, and every feature change becomes a
five-folder safari. Composition root at the app entry: build services once,
inject down.

### 6. Concurrency placement rules — read the build settings first

Where code runs now depends on two target settings, and Xcode 26 sets them
differently for new and existing projects: **Default Actor Isolation** is
`MainActor` for NEW projects and `nonisolated` for existing ones, and
**Approachable Concurrency** (SE-0461, `NonisolatedNonsendingByDefault`) is an
opt-in that makes `nonisolated async` functions run on the CALLER's actor.
Check both before teaching where anything executes.

- Under MainActor default + caller-actor async: the ViewModel is main-actor
  with no annotation, and a service it calls does its work ON main unless the
  method is `@concurrent` or the service is an `actor`. "Async means
  background" is the old mental model, and it is now wrong.
- Under the classic settings: annotate the ViewModel `@MainActor`; services
  return values, and the hop back is the caller's actor, expressed in types.
- In both worlds: no `DispatchQueue.main.async`; long work in `.task {}` (it
  cancels with the view — teach it over manual Task storage); shared mutable
  caches behind an `actor`. A Sendable complaint usually means ownership is
  unclear — fix the ownership, not the warning.

## Resources

- Sibling skills: [code-review](../code-review/SKILL.md) (these rules as
  review findings), [debugging](../debugging/SKILL.md) (when state bugs need
  hunting)
- Architecture-level decisions (modularization, dependency graphs):
  [architect](../../../architect/AGENTS.md)
