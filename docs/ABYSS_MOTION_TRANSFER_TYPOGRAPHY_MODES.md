# ABYSS — Motion Transfer & Typography Modes

This document defines three separate production modes. Never combine them implicitly. The operator must choose exactly one mode for each render.

## Shared input contract
- SOURCE IMAGE: the approved still image; it is the visual source of truth.
- REFERENCE GIF/VIDEO: reference for motion and/or style only, depending on the selected mode.
- TEXT INPUT: exact copy supplied by the operator when typography is generated.
- OUTPUT: vertical 9:16, 1080x1920, 30 fps, H.264 MP4 unless another delivery spec is supplied.

## Mode 1 — Motion only (default when the request says “solo movimiento”)
**Goal:** transfer the temporal movement from the reference, and nothing else.

### Prompt
Use SOURCE IMAGE as the immutable visual source. Analyze REFERENCE GIF frame by frame and extract only its temporal motion: camera path, translation, rotation, scale, timing, acceleration, easing, object trajectories and particle trajectories where separable.

Apply those motion parameters to SOURCE IMAGE. Do not transfer the reference's palette, lighting, contrast, texture, material, drawing style, facial features, anatomy, background design or typography.

Preserve the source image's geometry and identity. Treat the subject as a coherent layer. Do not use generative face reconstruction, morphing, liquify, mesh warping, elastic deformation or unconstrained optical flow. Use rigid transforms and masked particle layers. If a region cannot be tracked reliably, keep it static rather than inventing pixels.

All existing text is a protected layer: preserve exact characters, spelling, font, kerning, line breaks and layout. Do not redraw or regenerate it. If text should move, move the complete text layer rigidly; otherwise keep it locked.

Temporal consistency is mandatory: no flicker, jitter, facial drift, contour swimming, letter changes or invented motion. Compare rendered frames with SOURCE IMAGE and reject any frame that changes the subject's identity or text.

**Rule:** reference supplies motion only; source supplies all appearance.

## Mode 2 — Motion + style
**Goal:** transfer both temporal movement and a defined visual treatment from the reference, while preserving the source subject and exact text content.

### Prompt
Use SOURCE IMAGE as the subject, composition and identity source. Use REFERENCE GIF/VIDEO as the source of (1) motion and (2) visual treatment only.

Extract the reference motion: camera path, translation, rotation, scale, timing, easing, object and particle trajectories. Separately analyze its visual treatment: palette, tonal range, contrast, grain, line quality, lighting character, material response and atmosphere.

Apply the extracted movement and visual treatment to SOURCE IMAGE, but do not copy the reference subject, face, anatomy, objects, logos or written content. The source subject's silhouette, proportions and recognizable details must remain stable. Style may affect rendering, not geometry.

Do not morph, liquify, stretch, melt, replace facial features or invent anatomical details. Use masks and separate layers; preserve text as a protected overlay. If style treatment makes text less legible, render the text above the styled image.

**Rule:** reference supplies motion + appearance treatment; source supplies subject, composition and content.

## Mode 3 — Style only + new typography from supplied text
**Goal:** borrow the reference's visual language, but create a new design using exact text supplied by the operator and a different, explicitly named font.

### Prompt
Use REFERENCE IMAGE/GIF/VIDEO only to analyze visual style: palette, contrast, lighting, texture, grain, line treatment, atmosphere, depth and graphic composition. Do not reproduce its motion, subject, face, objects, logos or original lettering.

Create a new composition around SOURCE IMAGE (if supplied) and the following exact text:
[PASTE EXACT TEXT HERE]

Typography requirements:
- Use a different typeface from the reference: [SPECIFY FONT FAMILY].
- Preserve the exact wording, accents, capitalization, punctuation and line order.
- Do not paraphrase, translate, autocorrect, omit or add words.
- Treat typography as vector/text layers, not as painterly image content.
- Keep letters crisp, correctly spelled, legible and stable.
- Define hierarchy, size, weight, tracking, leading and alignment deliberately.
- Do not imitate the reference font; only transfer the broader visual language.

No motion transfer. Use a static design unless animation is explicitly requested.

**Rule:** reference supplies style only; supplied text supplies the exact copy; selected font supplies the typography.

## Technical safeguards
1. Separate subject, background, particles and text into independent layers/masks.
2. Prefer rigid transforms and tracked masks over dense optical-flow warping.
3. Use optical flow only for genuinely deformable elements such as smoke, liquid or particles, never for faces or typography.
4. Preserve original alpha and source resolution where possible; upscale with a high-quality resampler only at final export.
5. Use frame interpolation only when it does not invent or deform details. Otherwise use frame duplication or motion-compensated rigid transforms.
6. Run temporal checks for face/shape drift, text OCR consistency, flicker and edge stability.
7. If no clean mask or reliable track exists, freeze that region. Fidelity takes priority over extra motion.

## Negative prompt / reject conditions
No face replacement, no facial beautification, no new beard/hair, no altered eyes/nose/mouth, no anatomy changes, no liquify, no melting, no elastic warping, no letter mutation, no spelling changes, no pseudo-text, no random glyphs, no flicker, no texture transfer in Mode 1, no style transfer in Mode 1, no motion transfer in Mode 3.

## Delivery checklist
- [ ] Mode selected explicitly: 1, 2 or 3.
- [ ] Exact text supplied (for Modes 1 and 2 if text exists; Mode 3 always).
- [ ] Font family supplied for Mode 3.
- [ ] 9:16 / 1080x1920 / 30 fps / H.264 checked.
- [ ] Subject geometry compared against source.
- [ ] Text checked character by character.
- [ ] No frame has facial, contour or typography deformation.
