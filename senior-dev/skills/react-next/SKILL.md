---
name: react-next
description: >
  Decision criteria for React/Next.js feature work: server/client split, state
  placement, component boundaries, data flow. Trigger: load when building or
  restructuring React components, pages, or data fetching in a React/Next.js
  app. Complements (does not replace) ~/.claude/skills/react-19 and nextjs-15.
license: Apache-2.0
metadata:
  author: jrodrigopuca
  version: "1.0"
---

## When to Use

- Creating or restructuring components, routes, or data flow in React/Next.js
- Deciding where state lives or where fetching happens
- Something re-renders too much, props drill too deep, or a component "does everything"

## Critical Patterns

### 1. Server by default, client by exception

In Next.js App Router, every component is a server component until it earns
`'use client'` with a concrete reason: event handlers, browser APIs, stateful
interactivity. Push the directive to the **leaves** — a client wrapper at the
top of the tree silently drags everything under it to the client. When in doubt,
split: server shell, small client island.

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

### 4. Data fetching: on the server, close to use, deduped

- Fetch in server components / route loaders; client-side fetching is for data
  that changes after interaction, and then a query library owns it — never a
  bare `useEffect` + `useState` pair.
- Fetch where the data is used, not hoisted to the top and drilled down;
  request deduplication makes colocated fetches cheap.
- Mutations go through Server Actions with revalidation, and the UI reflects
  pending/error states — no fire-and-forget.

### 5. Composition before configuration

When a component sprouts boolean props (`isCompact`, `withHeader`, `hideFooter`),
stop: that's three components wearing a trench coat. Prefer `children` and slot
props over prop flags; prefer wrapping over forking.

### 6. Re-render hygiene is structural, not memo-spam

React 19 + Compiler make manual `useMemo`/`useCallback` mostly obsolete. When
something re-renders too much, fix the STRUCTURE first: state living too high
(ladder rung too big), context holding fast-changing values, components defined
inside components. Memoization patches what placement should have prevented.

## Resources

- API-level patterns: `~/.claude/skills/react-19/SKILL.md`,
  `~/.claude/skills/nextjs-15/SKILL.md`, `~/.claude/skills/zustand-5/SKILL.md`
- Sibling skill: [fullstack-boundaries](../fullstack-boundaries/SKILL.md) — where
  the component tree meets the wire
