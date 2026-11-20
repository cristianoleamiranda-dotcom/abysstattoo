# ABYSS TATTOO STUDIO — A VISTA / BLACK

Editable campaign workspace on the isolated branch `feat/abyss-black-friday-hyperframes`. No changes are made to `main`, other projects, or Dropbox originals.

## Approved creative direction

**02 — CORTE** is approved by the client on 20 Nov 2026.

- Core mechanic: diagonal typography rotated **−9°** crossing the image.
- Typography: **BLACK** solid; **FRIDAY** outline.
- Poster palette: BLACK `#080808`, OBSIDIAN `#14100D`, BONE `#B5A295`, CREAM `#EAE3DD`; chrome only as a restrained reflection.
- Poster typography: Anton + Inter.
- Campaign signature: **A VISTA / BLACK**.
- Brand: ABYSS TATTOO STUDIO.
- No retail yellow/red, discount bursts, floating prices, carts, gratuitous glitch or cyberpunk styling.

The editable poster layout is in `poster/02-corte/`. Its real-image slot is intentionally empty until the approved source photo is placed in the project. The template does not invent tattoos, people, jewelry, equipment, studio interiors or an emblem.

## Approval protocol

1. References and brief → three distinct low-resolution directions.
2. Client approval → high-resolution poster.
3. Poster review/approval → motion graphics.
4. Motion approval → kinetic typography.
5. Kinetic approval → edit and animate the supplied real audiovisual material.

The client has approved direction **02 — CORTE**. That authorizes work on this direction only; it does not authorize inventing campaign terms, a CTA, prices, discounts, dates, or replacing real source imagery. High-resolution final artwork remains dependent on the original approved photo and emblem being present in this branch.

## Project structure

- `poster/02-corte/index.html`: editable 4:5 poster layout template.
- `poster/02-corte/README.md`: asset requirements and rendering gate.
- `DECISION_02_CORTE.md`: approval record and scope.
- `index.html` and `compositions/`: initial HyperFrames motion sandbox. These are not yet the approved campaign film and must not be rendered as final.
- `SPEC.md`: approved visual system and stage gates.
- `assets/footage/`: approved source footage, when supplied.
- `assets/audio/`: licensed audio, when supplied.

## Important production status

This branch currently contains editable source and a poster layout template, **not a finished high-resolution poster or rendered video**. The poster requires the real approved source photograph and original emblem file. Motion work remains gated until the poster itself is materialized and approved.

No promotion terms are invented. Do not add offer values until ABYSS confirms them.

## HyperFrames sandbox

The existing HyperFrames scaffold is retained as an isolated technical workspace. Its original 30-second timing is provisional and does not supersede the campaign's existing 24.20-second kinetic master or the approved stage order.

Requires Node.js 22+ and FFmpeg in a compatible desktop/cloud environment:

```bash
cd campaigns/abyss-black-friday-hyperframes
npx hyperframes check --json
npx hyperframes preview
```

The CLI has not yet been run in this environment. Do not describe the scaffold as validated or rendered.
