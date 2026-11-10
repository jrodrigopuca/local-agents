---
name: lh-visual-direction
description: >
  Giving an interface a look of its own instead of the default one: sourcing
  the direction from the product's world, writing it down, and testing it
  for genericness. Trigger: load before a high-fidelity mockup, a landing
  page, a new visual identity or an icon set for a product with no
  established design system, or when asked to make an interface distinctive,
  on-brand, or less generic. Inside an existing design system, the system is
  the direction: lh-visual-craft.
license: Apache-2.0
metadata:
  author: jrodrigopuca
  version: "1.0"
  local-agents-id: "sk-08edf6"
---

## Critical Patterns

### 1. What is already given is the direction

A brand guide, a logo, a design system, a reference the user points at: read
them first and follow them exactly, even where they ask for a common look.
Distinctive is not a license to override the client. With nothing given, the
direction is yours to propose — say that it is a proposal, and that the next
patterns are how you got to it.

### 2. Source it from the product's world, not from other interfaces

The default look comes from drawing an interface that resembles other
interfaces. Start somewhere else: who uses this, for what job, and what does
that world look like off the screen? Its objects, materials, documents,
signage, instruments, vocabulary. A freight tracker lives among manifests,
stencilled container codes and hi-vis colours; a bike repair shop among
work stands, tyre labels and grease-pencil job tags. Write five to eight such
observations before choosing a single colour — the direction is picked FROM
that list, and each choice can say which observation it came from.

### 3. Write the direction down before any high-fidelity pixel

One short block, delivered with the mockup:

- **Concept** — one sentence a non-designer could repeat.
- **Palette** — four to six named colours, each with its role.
- **Type** — the roles (display, body, data) and why these faces: one family,
  or two that are plainly different.
- **Shape language** — corner radius, stroke weight, the angles in play,
  flat or layered.
- **Density and rhythm** — airy or packed, and where the layout breathes.
- **The signature** — the ONE element this product will be recognised by.
- **What it deliberately does not do.**

Then a wireframe of the layout concept (the wireframe rung of
[lh-mockups](../lh-mockups/SKILL.md)). The colour and type names in this
block become the tokens the mockup declares.

### 4. Second pass: the swap test

Read the direction back, line by line, asking one question: would this sit
unchanged in a different product? What would, nobody chose — revise it.
A default is not a banned thing; it is a choice made by habit. The habits of
the moment, to question and not to forbid: a neutral geometric sans picked
without looking, a purple-to-blue gradient, identical rounded cards with a
soft grey shadow, a centred hero over three feature columns, a tracked
uppercase label above every heading, emoji standing in for icons, a fade-up
on every block. Whatever replaces them out of habit is the next default: a
"safe alternative" palette or font is still one nobody chose.

### 5. One loud thing, and restraint around it

The signature carries the identity; everything else stays quiet so it can.
Three statement elements on one screen cancel each other. Structural devices
— rules, numbering, labels, badges — have to carry information: numbers only
where there is a sequence, a label only where the content needs one. Before
calling it finished, remove one accessory and look again; if nothing is
lost, it stays out.

### 6. Distinctive inside usable

- The floors of [lh-visual-craft](../lh-visual-craft/SKILL.md) (hierarchy,
  contrast, the spacing and type scales) and the flow from
  [lh-ux-flows](../lh-ux-flows/SKILL.md) are not negotiable for style.
- Where the screen is a tool — a dashboard, a form, a table — users bring
  conventions, and novelty in layout costs them time. Identity there comes
  from type, colour, density, iconography ([lh-icons](../lh-icons/SKILL.md))
  and the small moments: the empty state, the confirmation, the way a row
  selects.
- Where the screen is a first impression — a landing page, an onboarding —
  composition is open too: lead with the most characteristic thing of the
  product's world, in whatever form fits it.
- Motion: one orchestrated moment per screen, plus motion that answers a
  user's action by showing what changed. Never a scatter of entrances.

### 7. Look at it, and run the logo test

A mockup you have not seen rendered is unverified: open it, or render and
capture it, when the environment allows, and say so when it does not. Then
cover the logo: could someone tell whose product this is, or at least what
kind? If it could belong to anyone, go back to #4.

## Resources

- Sibling skills: [lh-mockups](../lh-mockups/SKILL.md) (the deliverable the
  direction travels with), [lh-visual-craft](../lh-visual-craft/SKILL.md)
  (the rules every direction still obeys), [lh-icons](../lh-icons/SKILL.md)
  (the icon style is derived from this direction)
