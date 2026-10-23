#!/usr/bin/env python3
"""Correct the baked-in typo in the supplied Abyss promotion without changing its design.

The original JPEG is preserved. The correction moves the original word "echas"
slightly to the right, inserts a matching italic "h", and saves a lossless PNG.
"""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets/promocion/abyss-promo-source.jpeg"
OUTPUT = ROOT / "assets/promocion/abyss-promo-corrected.png"
FONT = ROOT / "assets/fonts/cormorant-garamond-400-italic.woff"

# Original lettering bounds at the 2048 × 2048 source resolution.
WORD_X0, WORD_X1 = 525, 661
WORD_Y0, WORD_Y1 = 1585, 1634
WORD_SHIFT = 24
WORD_BASELINE = 1622
INSERT_X = 529
FONT_SIZE = 44
SUPERSAMPLE = 4


def main() -> None:
    original_bgr = cv2.imread(str(SOURCE), cv2.IMREAD_COLOR)
    if original_bgr is None:
        raise FileNotFoundError(f"No se pudo leer: {SOURCE}")
    if original_bgr.shape[:2] != (2048, 2048):
        raise ValueError(f"Se esperaba el afiche 2048 × 2048; llegó {original_bgr.shape[1]} × {original_bgr.shape[0]}.")
    if not FONT.exists():
        raise FileNotFoundError(f"Falta la fuente de corrección: {FONT}")

    gray = cv2.cvtColor(original_bgr, cv2.COLOR_BGR2GRAY)
    roi_gray = gray[WORD_Y0:WORD_Y1, WORD_X0:WORD_X1]

    # Build a local mask from the pale text, then expand it slightly to remove
    # its JPEG/antialias fringe before moving the original glyphs.
    word_mask = np.zeros_like(gray, dtype=np.uint8)
    local_mask = np.where(roi_gray > 38, 255, 0).astype(np.uint8)
    local_mask = cv2.dilate(local_mask, np.ones((3, 3), np.uint8), iterations=1)
    word_mask[WORD_Y0:WORD_Y1, WORD_X0:WORD_X1] = local_mask
    cleaned_bgr = cv2.inpaint(original_bgr, word_mask, 5, cv2.INPAINT_TELEA)

    # Preserve the exact shapes of the original "echas" letters and their
    # spacing; only shift them enough to make room for the missing initial h.
    rgb_original = cv2.cvtColor(original_bgr, cv2.COLOR_BGR2RGB)
    clean_rgb = cv2.cvtColor(cleaned_bgr, cv2.COLOR_BGR2RGB)
    source_word = rgb_original[WORD_Y0:WORD_Y1, WORD_X0:WORD_X1].astype(np.float32)
    source_gray = roi_gray.astype(np.float32)
    alpha = np.clip((source_gray - 14.0) / 222.0, 0.0, 1.0)
    alpha[source_gray < 28] = 0.0

    core = source_word[source_gray > 215]
    if core.size:
        ink = np.median(core, axis=0).astype(np.float32)
    else:
        ink = np.array([241.0, 237.0, 235.0], dtype=np.float32)

    dst_x0 = WORD_X0 + WORD_SHIFT
    dst_x1 = WORD_X1 + WORD_SHIFT
    destination = clean_rgb[WORD_Y0:WORD_Y1, dst_x0:dst_x1].astype(np.float32)
    composited = destination * (1.0 - alpha[..., None]) + ink[None, None, :] * alpha[..., None]
    clean_rgb[WORD_Y0:WORD_Y1, dst_x0:dst_x1] = np.clip(composited, 0, 255).astype(np.uint8)

    # Insert only the missing glyph, in a complementary high-contrast italic
    # serif. Supersampling keeps its diagonal edges crisp at the source size.
    base = Image.fromarray(clean_rgb, mode="RGB").convert("RGBA")
    glyph = Image.new("RGBA", (2048 * SUPERSAMPLE, 2048 * SUPERSAMPLE), (0, 0, 0, 0))
    font = ImageFont.truetype(str(FONT), FONT_SIZE * SUPERSAMPLE)
    draw = ImageDraw.Draw(glyph)
    draw.text(
        (INSERT_X * SUPERSAMPLE, WORD_BASELINE * SUPERSAMPLE),
        "h",
        font=font,
        fill=(int(ink[0]), int(ink[1]), int(ink[2]), 255),
        anchor="ls",
    )
    glyph = glyph.resize((2048, 2048), Image.Resampling.LANCZOS)
    corrected = Image.alpha_composite(base, glyph).convert("RGB")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    corrected.save(OUTPUT, format="PNG", optimize=True, compress_level=9)
    print(f"Afiche corregido y guardado sin pérdida: {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
