# ABYSS TATTOO STUDIO — BLACK FRIDAY

Editable HyperFrames campaign project. This is an isolated campaign workspace on branch `feat/abyss-black-friday-hyperframes`; it does not change `main` or any other project.

## Creative direction
**HYBRID CINEMATIC** — luxury editorial meets dark industrial craft.

- Format: 1080 × 1920, vertical 9:16
- Duration: 30 seconds
- Frame rate target: 30 fps
- Palette: obsidian, graphite, bone, restrained chrome
- Motion: kinetic typography, mask reveals, editorial cuts, camera-like graphic moves
- Story: hook → studio → tattoo → piercing → machines → gift card → brand end card

## Project structure
- `index.html`: master timeline and scene order
- `compositions/`: individually editable scenes
- `SPEC.md`: visual and timing specification
- `assets/footage/`: place approved studio, tattoo, piercing, machine and gift-card footage here
- `assets/audio/`: place licensed music and sound design here

## Important media note
The first commit is an **editable motion-design skeleton / storyboard**, not a finished commercial. Media panels are intentionally labelled placeholders. Replace them with real, approved ABYSS footage and product images before final render. Do not generate or imply real tattoos, piercings, equipment or studio interiors that are not present in the supplied source material.

## Run locally
Requires Node.js 22+ and FFmpeg, plus a desktop Chrome-compatible environment for rendering.

```bash
cd campaigns/abyss-black-friday-hyperframes
npx hyperframes check --json
npx hyperframes preview
```

If the CLI reports missing project scaffolding, initialize a separate temporary HyperFrames project with `npx hyperframes init` and compare its generated config; do not overwrite this campaign's source files blindly.

## Editing workflow
1. Replace each scene's labelled media slot with approved footage in `assets/footage/`.
2. Edit headlines and timings in the corresponding composition HTML.
3. Run `npx hyperframes check --json` and fix all errors.
4. Review snapshots and the full preview before rendering.
5. Render only after approving the preview.

## Commercial copy
No discount, price, date, availability or promotion terms are invented in this project. Add verified campaign conditions only after ABYSS approves them.
