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
2. @State       — view-local, transient (toggle, text field, sheet visibility)
3. @Binding     — owned above, mutated here
4. @Observable  — screen/feature state, owned by a ViewModel
5. Environment  — cross-cutting reads (theme, session) — injection, not a junk drawer
6. App-level    — one composition root owning shared services/models
```

`@State` holding what a ViewModel should own, and Environment used as a
global variable, are the two chronic misplacements.

### 3. MVVM, the honest version

- **View**: declares UI as a function of state; forwards intent
  (`vm.didTapSave()`); computes nothing business-y.
- **ViewModel** (`@Observable`, `@MainActor`): screen state as an enum
  (`loading / loaded(Data) / empty / error(String)` — make illegal
  combinations unrepresentable, per the senior-dev's types-as-design rule),
  intent methods, zero `import SwiftUI`.
- **Services**: protocol-fronted (`protocol InvoiceRepository`), injected by
  init, async APIs. The protocol is what makes the ViewModel testable with a
  fake — that's dependency injection earning rent, not ceremony.
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

### 6. Concurrency placement rules

UI state mutations on `@MainActor` (annotate the ViewModel, not individual
hops); services do their work off-main and return values (no
`DispatchQueue.main.async` — crossing back is the caller's actor, expressed
in types); long work in structured `Task`s tied to view lifetime
(`.task {}` modifier auto-cancels — teach it over manual Task storage);
shared mutable caches behind an `actor`. When the compiler complains about
Sendable, the design is usually telling you ownership is unclear — fix the
ownership, not the warning.

## Resources

- Sibling skills: [code-review](../code-review/SKILL.md) (these rules as
  review findings), [debugging](../debugging/SKILL.md) (when state bugs need
  hunting)
- Architecture-level decisions (modularization, dependency graphs):
  [architect](../../../architect/AGENTS.md)
