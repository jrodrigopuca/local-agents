---
name: react-next
description: >
  Decision criteria for React/Next.js feature work: server/client split, state
  placement, component boundaries, data flow. Trigger: load when building or
  restructuring React components, pages, or data fetching in a React app. The
  server/client and data-fetching patterns apply to Next.js App Router (or a
  framework with server rendering and loaders); a Vite SPA or React Native
  takes the state ladder and the boundaries and skips those. Complements (does
  not replace) any `react-19` / `nextjs-*` skill the host exposes.
license: Apache-2.0
metadata:
  author: jrodrigopuca
  version: "1.1"
---

_Verified against React 19, React Compiler 1.0 and Next.js 16 (September
2026). Two facts here are version-bound — whether the compiler is on, and what
Next caches by default — so when the year or the major has changed, re-check
them before teaching._

## Critical Patterns

### 1. Server by default, client by exception

In Next.js App Router, every component is a server component until it earns
`'use client'` with a concrete reason: event handlers, browser APIs, stateful
interactivity. Push the directive to the **leaves** — a client wrapper at the
top of the tree silently drags everything under it to the client. When in doubt,
split: server shell, small client island. In a client-only app (Vite, React
Native, a pure SPA) this pattern has nothing to apply to — everything is
client, and saying so beats forcing a server/client split that buys nothing.

### 2. The state placement ladder

Place state at the LOWEST rung that satisfies the requirement, and be able to
name why it can't live one rung lower:

```
1. Derived           — computed from existing state/props: don't store it, compute it
2. Local (useState)  — one component cares
3. Lifted            — siblings share it: nearest common parent
4. URL               — survives refresh/share/back button (filters, tabs, pagination)
5. Server state      — cache of remote data: fetch layer owns it, not useState
6. Global store      — genuinely app-wide (session, theme); the LAST resort, not the first
```

Most state bugs are state living rungs above where it belongs. URL state (rung
4) is the most underused rung — reach for it before any store.

### 3. Component boundaries follow responsibility, not visuals

Split components when responsibilities diverge (fetching vs. rendering, form
logic vs. field display), not when a file "looks long". Container/presentational
still earns its keep: presentational components take data and callbacks, know
nothing about where data comes from, and are trivially testable.

### 4. Data fetching: on the server, close to use, deduped — and never assume the cache

- Fetch where the framework renders on the server: Server Components in Next
  App Router, loaders in Remix / React Router / TanStack Start (Next has no
  loaders). Client-side fetching is for data that changes after interaction,
  and then a query library owns it — never a bare `useEffect` + `useState`
  pair.
- Fetch where the data is used, not hoisted to the top and drilled down;
  per-request memoization (React's `cache()`, the framework's fetch dedup)
  makes colocated fetches cheap within one render.
- **What is cached by default is a property of the Next MAJOR and its config,
  and it has flipped:** 14 cached `fetch` by default, 15 stopped, 16 with
  Cache Components caches nothing until a function or page says
  `'use cache'`. Read the version and `next.config` before assuming anything
  is cached or fresh, and say which version your advice targets.
- Mutations go through Server Actions with revalidation, and the UI reflects
  pending and error states (`useActionState` gives you both) — no
  fire-and-forget.

### 5. Loading and failure boundaries are placed, not sprinkled

A `Suspense` boundary goes around the unit the user can wait for SEPARATELY —
the slow panel, not the whole page — so streaming shows the rest while it
loads; one boundary at the root is a spinner with extra steps. An error
boundary goes per route segment (`error.tsx`) so a failing widget doesn't
blank the app. State that must reset when its subject changes (a form for a
different record, a list for a different query) resets by `key`, not by
effects that clear it.

### 6. Composition before configuration

When a component sprouts boolean props (`isCompact`, `withHeader`, `hideFooter`),
stop: that's three components wearing a trench coat. Prefer `children` and slot
props over prop flags; prefer wrapping over forking.

### 7. Re-render hygiene is structural, not memo-spam

Manual `useMemo`/`useCallback` become mostly unnecessary only when the **React
Compiler is on** — it shipped 1.0 in October 2025 and Next.js 16 supports it
stable, but it is OFF until the project sets `reactCompiler: true` (or the
babel plugin). React 19 by itself memoizes nothing. Check the config before
deleting memoization, and before adding it. Either way, when something
re-renders too much, fix the STRUCTURE first: state living too high (ladder
rung too big), context holding fast-changing values, components defined inside
components. Memoization patches what placement should have prevented.

## Resources

- API-level patterns: a `react-19`, `nextjs-*`, or `zustand-*` skill if the host
  exposes one — all ship outside this catalog, so treat them as optional and fall
  back to each framework's current docs, stating the version you targeted
- Sibling skill: [fullstack-boundaries](../fullstack-boundaries/SKILL.md) — where
  the component tree meets the wire
