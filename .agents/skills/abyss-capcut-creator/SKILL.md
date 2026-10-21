---
name: abyss-capcut-creator
description: Apply CapCut Creator level-growth principles, template-editability guidance, motion design, FFmpeg media QA, and Community Guidelines checks to Abyss Tattoo Studio promotional videos. Use when reviewing, remastering, preparing templates, or publishing CapCut creator content.
---

# Abyss · CapCut Creator workflow

Use this workflow for original vertical promotional videos and reusable CapCut templates. Treat the scoring details below as the creator-program guidance supplied by the account owner (last updated May 2024); CapCut can change formulas, thresholds, eligibility and UI. Never promise points, level gains, views, export counts, campaign approval, or FYF eligibility.

## 1. Pick a growth strategy from the current level

CapCut recalculates points daily (with the stated content-value, bonus, and penalty schedules below). Total points are described as:

`Activity + Streak + Domestic Exports + Global Exports + Content Value + Bonus − Inactivity Penalty − Eco Penalty`

- **Levels 0–3:** establish a sustainable publishing cadence and daily streak with distinct, useful templates. Avoid thin duplicates or spam; add real personalization and usability to every post.
- **Level 4 and above:** activity points have a ceiling; prioritize user value, trend-fit, domestic exports first, then global reach and off-platform impact. Localize on-screen copy and templates rather than merely changing hashtags.
- **Any level:** join relevant official bonus events; keep approved templates live; avoid deleting published work. Never buy, exchange, or automate engagement. No fake likes, comments, views, exports, or misleading incentives.

The stated update cadence is: activity, streak, domestic/global exports daily (shown next day); content-value weekly (Tuesday); inactivity weekly (Tuesday); event bonus no later than five business days after the event; Eco deductions may follow deletions, failed review, or community violations. These are not guaranteed service-level times—verify current in-app documentation.

## 2. Design for real template reuse

1. Establish a one-sentence audience promise and opening hook in the first 1–2 seconds.
2. Use a clear visual story, readable mobile-safe type, high contrast, purposeful cuts, and a single prominent CTA.
3. Make fields users genuinely need to personalize native CapCut text layers (for an event invitation: date, time, venue, dress code, RSVP). Keep these separate from flattened footage; preserve a clean background plate for each text-bearing scene.
4. Keep a coherent motion personality. Stage one hero action at a time; use secondary and ambient motion sparingly. Entrances decelerate, exits accelerate, and ambient loops should be subtle. Respect reduced-motion contexts in web previews.
5. Use original/cleared media and music. Record provenance and permitted use; platform library licenses can differ between template creation, export, and external reuse.
6. Write a truthful title and localized caption; include only campaign-required hashtags, with no unrelated tag stuffing. Recheck each event's task page before posting.

## 3. Safety, authenticity, rights, and broad-recommendation review

Manually inspect every clip, thumbnail, text layer, audio track, caption, and link. Reject or revise content that threatens or glorifies violence, depicts graphic injury/blood, promotes dangerous acts, controlled substances, weapons, gambling, scams, hate, harassment, sexual exploitation, youth endangerment, or personal-data exposure. Do not use sexualized minors, private information, unverified QR codes, fabricated claims, fake engagement, or other people's watermarks.

For a broad-audience/FYF-safe cut, additionally avoid jump scares, gore-like tattoo process shots, distressing injury, excessive adult drinking, suggestive framing, unverified ads, or reused footage without creative transformation. Do not promote buying/selling alcohol or tobacco; when event drinks are not essential, use clearly non-alcoholic/mocktail visuals. Ensure all people depicted are adults where the context requires it. Never claim a video is “guaranteed eligible”; recommendation eligibility and moderation are platform decisions.

## 4. Technical gates

- Start with source files locally available in the project; preserve immutable originals.
- For web-scrub/backbone assets, use the repository's `references/video-pipeline-upstream.md` as a starting point: short GOP, faststart, sensible CRF, and explicit probing. Adapt dimensions/bitrate to the actual use; do not force a 1080×1620 profile onto 9:16 deliverables.
- Run `python3 scripts/audit_creator_assets.py --profile creator-vertical <files...>` before delivery. This verifies video stream presence, dimensions, duration, frame rate and audio-track presence. It cannot inspect visual policy compliance, editability, ownership, music license, legibility, or actual CapCut review; complete the manual checklist above.
- For campaign-specific templates, compare duration, scene count, required details, hashtags, and editable areas against the current official mission payload. Record failures rather than silently claiming compliance.
- Apply `references/qa-verify-upstream.md`: verify server response and critical assets before announcing a live preview; state any unverified areas.

## 5. Input handling and limitations

Temporary file-sharing URLs can expire and may not be reachable from the build environment. Do not report analysis of footage that was not downloaded and inspected. Ask for the actual files or stable accessible links; then run metadata QA and visual review against each asset. Never upload user footage to a third party without the user's request.

## 6. Output checklist

- [ ] Source and rights/provenance recorded.
- [ ] Technical audit passes for the intended channel.
- [ ] Manual Community Guidelines / FYF review completed.
- [ ] Template text remains editable; preview/export remains readable on a phone.
- [ ] Title/caption/required tags checked against current campaign.
- [ ] Direct downloads and live preview tested; incomplete work and uncertainty disclosed.
