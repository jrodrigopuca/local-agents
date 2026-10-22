# Agent emblems

One SVG per agent, 256×256: the roster as a tribe of masks. They are for
humans (README, REFERENCE.es.md, slides, a host that shows an avatar).
Nothing in the install path reads them, and `validate.py` does not check
them. Each file is self-contained: no fonts, no text, no external
references.

## The system

- **One shape.** Every mask is the same tall oval on a dark tile
  (`#17191F`, corner radius 60). The shape is shared because the agents
  are one model wearing different roles: the mask is the role.
- **Two colours per mask.** The body is the family's material; a zone in
  the agent's own colour (a half, a band, a diagonal, a veil, a column)
  says who it is. Material and zone differ in value, not only in hue, so
  the pair still reads at 48 px.
- **Carved, not drawn.** Eyes are openings, never expressions; every mask
  has a carved nose and no mouth. Eyes and marks are cut in the tile
  colour.
- **Two marks.** The forehead mark says how the agent works (the loop,
  `< >`, the cadence ring, the converging dots). The chin mark repeats the
  family for readers who do not tell the colours apart.
- **Palette.** Five base colours and their tints and shades: `#38A5AD`,
  `#F09F42`, `#EA3E3E`, `#801446`, `#451D6D`. Violet and wine are
  lightened for the material so the carving stays legible.

| Family | Material | Chin mark | Agents |
|---|---|---|---|
| Base | wine, lightened `#B97E99` | none | generalist |
| Engineering | teal `#38A5AD` | beads | senior-dev, qa, dba, devops, data-ml, apple-dev |
| Product & design | orange `#F09F42` | two bars | product-manager, ux-ui, gamification |
| Judgment & coordination | violet, lightened `#A28EB6` | plumb line | architect, eng-manager |
| Archetypes | red `#EA3E3E` | diamond | visionary, stark, security |

## The masks

| Agent | Zone | Forehead mark |
|---|---|---|
| [generalist](generalist.svg) | a band across the eyes, the plain domino | the loop |
| [senior-dev](senior-dev.svg) | the right half, lighter: two halves, pairing | `<` and `>` |
| [qa](qa.svg) | split by a lightning seam | a carved X: the case crossed out |
| [dba](dba.svg) | the base, data as the foundation | two interlocked rings |
| [devops](devops.svg) | two rails framing the eyes | a ring of notches, one per run |
| [data-ml](data-ml.svg) | a diagonal split: the fitted line | dots converging from four to one |
| [apple-dev](apple-dev.svg) | a white forehead band | two dots rising to an open circle |
| [product-manager](product-manager.svg) | a forehead cap pointing to the eyes | a target |
| [ux-ui](ux-ui.svg) | a half with a curved seam | circle, square, triangle |
| [gamification](gamification.svg) | a rank chevron | a star in a dotted ring |
| [architect](architect.svg) | an X of colour born at the third eye: four sectors | three equal eyes |
| [eng-manager](eng-manager.svg) | a central column joining brow and chin | a three-node hub |
| [visionary](visionary.svg) | a forehead cap, one vision slit | a four-point star |
| [stark](stark.svg) | a single gold T over slit eyes | a small core |
| [security](security.svg) | a veil over the lower face | a hood band and a keyhole |

Designed by the `ux-ui` agent over seven iterations with the maintainer
(2026-10-22). Earlier versions are in the git history of this folder.
To change one, edit its SVG by hand; keep the oval, the two-colour rule
and the family material.
