# ABYSS — Pose Transfer Noir Portrait

## Objective
Create a photorealistic black-and-white portrait that preserves Cristian's real facial identity and body details while transferring only the pose from the supplied pose reference.

## Reference roles
- **Identity / appearance reference:** the user's own outdoor portraits and the approved rain-soaked noir portrait. Preserve face shape, eyes, nose, lips, beard density and outline, hairline, natural skin texture, chest/wing tattoo design, and crystal pendant.
- **Pose reference:** the latest supplied frontal close-up showing both hands placed behind the head, elbows extending toward the upper corners, head slightly forward, and direct eye contact with the camera. This image is a pose guide only; do not copy its model's face or identity.

## Exact pose to reproduce
- Both hands behind the head, fingers naturally resting in / holding the hair.
- Frontal, symmetrical head-and-shoulders composition.
- Eyes looking straight into the lens.
- Head upright with a very slight forward inclination; no upward-looking or three-quarter pose.
- Tight portrait crop, include both hands and forearms entering from the upper edges, shoulders visible.
- Keep anatomy natural: five fingers per hand, believable wrists and elbows.

## Visual direction
- Monochrome black and white, high-contrast editorial noir.
- Wet hair and realistic water droplets across forehead, cheeks, beard, neck and shoulders.
- Dark seamless background with controlled silver rim light.
- Retain the user's own chest tattoo and crystal pendant where visible; do not invent, redesign, mirror or relocate tattoos or jewelry.
- Realistic pores, beard strands and wet-skin highlights; no plastic skin or excessive sharpening.

## Recommended generative workflow
1. Use the identity portrait as the image/reference input.
2. Extract pose skeleton from the pose reference with DWPose / OpenPose.
3. Apply the pose map with ControlNet OpenPose (or equivalent pose conditioning).
4. Use IP-Adapter FaceID / InstantID or the platform's identity-reference control at moderate-to-high identity strength.
5. Inpaint hands, hairline and shoulders separately if needed; inspect finger count and wrist anatomy.
6. Restore fine details conservatively; do not use face beautification or face-shape correction.
7. Finish with monochrome grading, wet-surface highlights and subtle film grain.

## Prompt
Photorealistic high-end black-and-white noir editorial portrait of the same man shown in the identity reference. Preserve his exact recognizable facial identity and natural proportions: same face shape, eyes, nose, lips, beard, hairline and skin texture. Reproduce the pose reference precisely: frontal head-and-shoulders close-up, both hands behind the head holding the hair, elbows extending toward the upper corners, head slightly inclined forward, eyes looking directly into the camera. Wet hair, realistic water droplets running naturally down forehead, cheeks, beard and neck. Dark seamless background, dramatic silver rim lighting, sculpted monochrome chiaroscuro, crisp realistic pores and beard strands. Preserve the man's own chest tattoo and crystal pendant wherever visible. Anatomically correct hands and fingers. Editorial photography, natural lens perspective, highly realistic.

## Negative prompt
Different person, face replacement, altered identity, generic model face, face slimming, changed nose, changed jaw, changed beard, changed hairline, upward gaze, looking away, profile, three-quarter view, raised chin, hands covering face, extra fingers, fused fingers, missing fingers, broken wrists, duplicated arms, deformed elbows, invented tattoos, altered tattoo design, missing pendant, extra jewelry, smooth plastic skin, CGI look, illustration, excessive sharpening, text, watermark.

## Delivery
- Master: 4:5 or 2:3 high-resolution still, depending on generator limits.
- Story crop: 9:16, 1080 × 1920.
- Review identity and pose separately before animation.
- Animate only after the still is approved; use a restrained 6–8 second push-in with subtle rain movement.
