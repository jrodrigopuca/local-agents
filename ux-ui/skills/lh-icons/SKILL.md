---
name: lh-icons
description: >
  Drawing icons and small graphics that belong to a brand and to each other:
  deriving the style from the brand, metaphor, grid and construction, spot
  graphics, and the SVG that leaves your hands. Trigger: load when asked to
  create or redraw an icon, an icon set, or a small illustration (an empty
  state graphic, a feature mark), to match icons to a brand or interface, or
  to judge whether an icon reads. Choosing where an icon goes on a screen is
  lh-visual-craft.
license: Apache-2.0
metadata:
  author: jrodrigopuca
  version: "1.0"
  local-agents-id: "sk-6ba324"
---

## Critical Patterns

### 1. Look at the family before drawing a member

An icon is never alone: it sits next to the others in the product. Find the
set in use first — the project's icon folder, the library it imports — and
read its rules off it: grid size, stroke weight, corner style, outline or
filled. If the set already has the icon, use it. If you add one, it follows
those rules even where you would choose differently; a better-drawn icon
that looks foreign is a worse icon.

### 2. No family yet: derive the style from the brand, and write it down

Icons that could ship in any product are the default, and they are why a set
feels generic. The style is read off what the brand already is:

- **The logo** — its angles, whether curves are circular or squared-off, how
  strokes end, any cut, gap or notch it uses.
- **The typeface** — geometric or humanist, stroke contrast, round or flat
  terminals. Icons sit beside text and should look drawn by the same hand:
  their stroke near the weight of the text's stems.
- **The interface** — corner radius and border weight of buttons and cards.
- The direction block, when there is one
  ([lh-visual-direction](../lh-visual-direction/SKILL.md) #3).

Turn that into a style spec before the first icon:

| Field | Example |
|-------|---------|
| Grid and padding | 24, drawing inside 20 |
| Stroke | 1.75, the weight of the text's stems |
| Caps and joins | flat caps, mitred joins (the typeface has flat terminals) |
| Corner radius | 2, the UI's small radius |
| Angles allowed | 0°, 45°, 90° |
| Fill model | outline; a solid twin for selected |
| Signature trait | the logo's clipped corner: one corner cut at 45° in each icon |

The signature trait is what makes the set this brand's: one small, repeatable
device present in every icon — an open gap, a cut corner, a dot, a single accent
shape. One trait, never two.

Draw three anchor icons first — one round, one boxy, one complex (a gear, a
person) — and judge the STYLE on them, side by side. Adjust the spec, not the
icons. Then the rest in batches of about five, each batch laid next to the
anchors before moving on.

### 3. The metaphor has to survive without its label

Pick the object or action people already associate with the meaning, then
test it: at 16px, with no text, would a new user guess it? When the concept
is abstract ("sync settings", "workspace"), the honest answer is usually no —
ship it with its label instead of inventing a symbol nobody learned. One
metaphor means one thing across the whole product. Where the product's world
has its own objects, prefer them over the universal one: the set gains
character exactly where the subject allows it, and stays conventional where
users rely on convention (search, close, back).

### 4. Grid and construction

Defaults when neither family nor spec sets them:

- **Canvas** 24×24, with 2px of padding: the drawing lives in 20×20.
- **Keyline shapes** for equal visual weight: a circle 20 across, a square 18,
  a wide rectangle 20×16, a tall one 16×20. A square drawn as large as the
  circle looks bigger than it.
- **One stroke weight**, one cap and join style, one corner radius, set on
  the root element and overridden nowhere without a reason.
- **Points on whole or half pixels**, two decimals at most, no transforms:
  the position is in the coordinates.

Then correct by eye: curves and points overshoot the keyline by about half a
pixel, and a triangle or play arrow centred by its bounding box looks
off-centre — nudge it until it looks right and keep the nudge.

Draw with paths, not only with primitives. A set built from bare circles and
rectangles is what reads as basic: real shapes need curves (`C`, `Q`, `A`
segments), a line that changes direction, a deliberate gap. Three or four
shapes at most; every detail has to survive at 16px, where gaps narrower
than the stroke fill in.

### 5. Graphics bigger than an icon

An empty-state graphic, a feature mark, an onboarding spot (64 to 200px) is
not a 24px icon scaled up — a lone glyph in a tinted circle is the default,
and it is why these read as placeholder.

- **One idea per graphic**, said with the product's own objects (#3).
- **Two or three layers of depth**: a ground shape, the subject, one accent
  detail overlapping the edge of something. Overlap is what makes it a scene.
- **The same shape language as the icons**: the spec's corners, angles and
  signature trait; the stroke scaled by one stated rule (say, 2 at 24px and 3
  at 96px), never left to whatever the scaling gives.
- **The direction's palette only**: two or three tones plus the accent, as
  custom properties so both themes work. Fills and cut-outs are welcome
  here; gradients and shadows only if the direction has them.
- **A family too**: three spot graphics share ground shape, layer count and
  accent placement, or they look like three sources.

### 6. The SVG that leaves your hands

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
     stroke="currentColor" stroke-width="1.75" stroke-linecap="butt"
     stroke-linejoin="miter">
  <path d="M4 7h16M10 11v6M14 11v6M6 7l1 12h10l1-12M9 7V4h4.5"/>
</svg>
```

- `viewBox` identical across the set, and no fixed size: the size comes from
  where the icon is used.
- `currentColor`, never a hex, for UI icons: they take the colour of the text
  beside them and follow the theme for free.
- No editor leftovers: ids, classes, transforms, clip paths, metadata, a
  white background rectangle.
- Named for what it depicts, in lowercase kebab-case (`trash`,
  `arrow-left`), not for one use of it (`delete-invoice`).
- Whether a control shows the icon alone is a screen decision; if it does, it
  needs an accessible name, and the spec says which.

### 7. Prove it in a sheet, and look at the sheet

Deliver the set with a specimen file, self-contained: the style spec at the
top; every icon at 16, 24 and 48, on the light and the dark surface; a row
beside the brand's logo and a line of its text; each icon once inside the
control it was made for. An SVG written as coordinates and never rendered is
unverified — open or capture the sheet when the environment allows, and say
so when it does not. On the sheet, look for the icon that is heavier,
larger or rounder than its neighbours, and for the logo test: with the logo
hidden, does the set still look like this brand's?

The SVGs, the spec and the sheet are design files — wiring them into the
product is the developer's (ux-ui's Handoffs).

## Resources

- Sibling skills: [lh-visual-direction](../lh-visual-direction/SKILL.md)
  (where the style comes from), [lh-visual-craft](../lh-visual-craft/SKILL.md)
  (size, colour and placement on the screen),
  [lh-mockups](../lh-mockups/SKILL.md) (the specimen sheet is a small mockup),
  [lh-dev-handoff](../lh-dev-handoff/SKILL.md) (naming and tokens)
