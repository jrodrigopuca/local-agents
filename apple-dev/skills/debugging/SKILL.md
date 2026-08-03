---
name: debugging
description: >
  Debugging Apple-platform issues as taught method: crashes, leaks, hangs,
  and weird behavior — Socratic first, tools named, root cause always.
  Trigger: load on crashes, memory leaks, hangs, "it behaves weird", or any
  "why is this happening?" in Swift/iOS/macOS.
license: Apache-2.0
metadata:
  author: jrodrigopuca
  version: "1.0"
---

## When to Use

- A crash, hang, leak, or inexplicable behavior
- "It works on simulator but not on device" (and all its cousins)
- Teaching the user to debug — which is the actual goal every time

## Critical Patterns

### 1. Debugging is the mentorship's best classroom — guide, don't grab

This is where "teach fishing" pays most: walk them through the METHOD with
Socratic steps ("what EXACTLY does the crash log say?", "what's the last
thing you know is true?"), because debugging skill compounds for life.
Exceptions per the [mentorship ladder](../../AGENTS.md): cryptic
tooling errors (code signing, DerivedData corruption, simulator weirdness)
get the answer straight — reserve the Socratic method for bugs that teach.

### 2. Read the crash before theorizing

Every crash diagnosis starts with the artifact, not the vibes:

| Crash says | It usually means |
|------------|------------------|
| `EXC_BAD_ACCESS` | Accessing freed memory — over-released object, dangling pointer, race |
| `Fatal error: Unexpectedly found nil` | A force unwrap met reality — read WHICH line, ask why the invariant broke |
| `EXC_BREAKPOINT` on a Swift runtime line | Failed precondition: array index, force cast, arithmetic |
| Main-thread checker / purple warnings | UI touched off main — actor isolation hole |
| Watchdog kill (`0x8badf00d`) | Main thread blocked too long at launch/foreground |

Symbolicate first if it's from the field; then find the LAST frame that's
YOUR code. The stack tells you where it died — the question to teach is
"where did the bad state get CREATED?", which is earlier.

### 3. The reproduction discipline (inherited, domain-tuned)

Same law as [qa's `bug-reporting`](../../../qa/skills/bug-reporting/SKILL.md) and the
[generalist's `verification`](../../../generalist/skills/verification/SKILL.md): reproduce
before fixing, one hypothesis at a time, binary-search the surface (comment
out half the view, mock the service, hardcode the input). Apple-specific
multipliers to check early because they explain "sometimes": simulator vs
device, debug vs release (optimization changes timing), first-install vs
upgrade (migration state), airplane mode, low-power mode, different OS
versions.

### 4. Memory leaks: prove the graph

Symptoms: memory climbing screen after screen, `deinit` never printing,
doubled network responses (two live instances subscribed). Method: add a
`deinit { print("...") }` to the suspect (the poor man's leak detector — it
teaches WHY), then Instruments' Leaks/Allocations or Xcode's Memory Graph
Debugger to SEE the retain cycle: who holds whom. The usual suspects are the
[code-review 🔴 list](../code-review/SKILL.md): strong `self` in stored
closures, strong delegates, long-lived `Task`s. Fix = ownership decision
(`weak`), not a random sprinkle of weakness until the symptom hides.

### 5. Hangs and jank: measure, then blame

Main-thread stalls have three usual causes: synchronous I/O on main (disk,
network, big decode), massive view recomputation (a `body` doing work — see
[state-architecture](../state-architecture/SKILL.md)), or layout thrash.
Don't guess between them: Time Profiler shows where main-thread time
actually goes ("performance is measured, not guessed" — the
[senior-dev rule](../../../senior-dev/AGENTS.md), same religion). Teach
reading the heaviest stack trace before touching any code.

### 6. Weird SwiftUI behavior: it's almost always identity or ownership

View not updating → who owns the state, is mutation reaching the owner, is
the model actually `@Observable`? Updating too much → observation too
coarse, body too big. State resetting mysteriously → view IDENTITY changed
(position in the tree, `.id()`, conditional branches) so SwiftUI built a new
view with fresh `@State`. Animation glitches → same identity story. Teach
the mental model — SwiftUI diffs a tree of descriptions; identity decides
what survives — and these bugs become predictable instead of spooky.

## Resources

- Sibling skills: [code-review](../code-review/SKILL.md) (the defect
  patterns), [state-architecture](../state-architecture/SKILL.md) (the
  ownership model these bugs violate)
- The debugging epistemics this domain-tunes:
  [generalist/verification](../../../generalist/skills/verification/SKILL.md),
  [senior-dev/pairing](../../../senior-dev/skills/pairing/SKILL.md) (co-debugging protocol)
