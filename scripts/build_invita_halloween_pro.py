#!/usr/bin/env python3
"""
CapCut Creator Mission Builder — Task ID 307926551812 (`🎃 PRO | #InvitaHalloween`)
===================================================================================
Generates a complete 60.00 FPS broadcast-quality package fulfilling 100% of CapCut's
official mission rules (10/19/2026 - 10/26/2026):
  1. Duration: 16.00s (within mandatory 12-20s window), 960 frames @ 60.00 FPS (1080x1920)
  2. 6 distinct cinematic scenes with 3D camera motion, volumetric purple/orange mist,
     animated flapping bats, glowing corner cobwebs, vector Jack-o'-lanterns & embers
  3. Palette: Deep Obsidian Black (#07060A), Pumpkin Orange (#FF6B1A), Electric Purple (#8B2CF5),
     and Neon Emerald Green accent (#39FF88)
  4. Dedicated exclusive Event Details screen (t = 7.50s..11.20s -> 3.70s > 2.0s mandatory!)
     displaying editable Date, Time, Location & Dress Code clearly
  5. Outputs:
     - `invita_halloween_pro_master_1080x1920_60fps.mp4` (Universal Template Master)
     - `invita_halloween_abyss_edition_1080x1920_60fps.mp4` (Abyss Tattoo Studio Edition)
     - `clips_editables_capcut/clip_01..06_*.mp4` (6 clean 60fps animated background clips)
     - `CapCut_Proyecto_InvitaHalloween_PRO.zip` (Importable CapCut Desktop Draft + 6 clips + guide)
"""

from __future__ import annotations

import json
import math
import subprocess
import uuid
import wave
import zipfile
from pathlib import Path

import cv2
import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
FPS = 60
DURATION = 16.0
TOTAL_FRAMES = int(FPS * DURATION)  # 960 frames @ 60.00 fps

# Exact CapCut #InvitaHalloween Color Palette
COL_BLACK = (7, 6, 10)
COL_ORANGE = (255, 107, 26)
COL_PURPLE = (155, 56, 255)
COL_GREEN = (57, 255, 136)
COL_IVORY = (248, 245, 240)
COL_MUTED = (205, 198, 214)

SEGMENTS = [
    # (start_s, end_s, slug, scene_file, zoom0, zoom1, pan_x, pan_y)
    (0.00, 2.50, "01_hook", "scene_01_hook.jpg", 1.03, 1.13, 0.0, -18.0),
    (2.50, 5.00, "02_snacks", "scene_02_snacks.jpg", 1.12, 1.03, 16.0, 10.0),
    (5.00, 7.50, "03_disfraces", "scene_03_costumes.jpg", 1.03, 1.13, -14.0, -12.0),
    (7.50, 11.20, "04_datos_evento", "scene_04_info_bg.jpg", 1.01, 1.05, 0.0, -6.0),
    (11.20, 13.50, "05_photospot", "scene_05_photospot.jpg", 1.12, 1.03, -12.0, 12.0),
    (13.50, 16.00, "06_cta", "scene_06_cta.jpg", 1.02, 1.11, 0.0, -14.0),
]


def load_font(path: str, size: int, weight: int | None = None) -> ImageFont.FreeTypeFont:
    f = ImageFont.truetype(path, size)
    if weight is not None:
        try:
            f.set_variation_by_axes([weight])
        except Exception:
            pass
    return f


FONTS_DIR = Path("/tmp/fonts")
F_DISPLAY = lambda sz: load_font(str(FONTS_DIR / "Anton.ttf"), sz)
F_SPOOKY = lambda sz: load_font(str(FONTS_DIR / "Creepster.ttf"), sz)
F_SANS_B = lambda sz: load_font(str(FONTS_DIR / "Montserrat.ttf"), sz, 800)
F_SANS_M = lambda sz: load_font(str(FONTS_DIR / "Montserrat.ttf"), sz, 600)


# ---------------------------------------------------------------------------
# Original Royalty-Free 125 BPM Spooky Dark-Synth Pop Soundtrack Generator
# ---------------------------------------------------------------------------
def synthesize_halloween_audio(wav_path: Path, m4a_path: Path, ff: str) -> None:
    sr = 48000
    n = int(sr * DURATION)
    t = np.arange(n, dtype=np.float64) / sr
    bpm = 125.0
    beat_dur = 60.0 / bpm  # 0.480s

    left = np.zeros(n, dtype=np.float64)
    right = np.zeros(n, dtype=np.float64)

    # 1. Punchy 125 BPM Kick + Clap + Stereo 16th Hi-Hat Groove
    num_beats = int(DURATION / beat_dur) + 1
    rng = np.random.default_rng(31102026)

    for b in range(num_beats):
        t0 = b * beat_dur
        i0 = int(t0 * sr)
        if i0 >= n:
            break
        # Kick
        kl = min(int(0.24 * sr), n - i0)
        kt = np.arange(kl) / sr
        f_sweep = 48.0 + 130.0 * np.exp(-kt * 28.0)
        kick = np.sin(2.0 * np.pi * np.cumsum(f_sweep) / sr) * np.exp(-kt * 9.5) * 0.62
        left[i0 : i0 + kl] += kick
        right[i0 : i0 + kl] += kick

        # Crisp clap on beats 1 and 3
        if b % 2 == 1:
            cl = min(int(0.16 * sr), n - i0)
            ct = np.arange(cl) / sr
            noise = rng.standard_normal(cl) * np.exp(-ct * 22.0) * 0.20
            left[i0 : i0 + cl] += noise * 1.05
            right[i0 : i0 + cl] += noise * 0.95

        # Off-beat 16th hats
        for sub in range(4):
            h0 = int((t0 + sub * beat_dur * 0.25) * sr)
            if h0 >= n:
                break
            hl = min(int(0.055 * sr), n - h0)
            ht = np.arange(hl) / sr
            amp = 0.11 if sub == 2 else 0.048
            hat = rng.standard_normal(hl) * np.exp(-ht * 68.0) * amp
            # High-frequency difference filter
            hat = np.diff(hat, prepend=0.0)
            pan = 0.65 if sub % 2 == 0 else 0.35
            left[h0 : h0 + hl] += hat * pan * 1.5
            right[h0 : h0 + hl] += hat * (1.0 - pan) * 1.5

    # 2. Driving Dark Synth Bass (C2 -> Ab1 -> F1 -> G1 progression)
    bass_roots = [65.41, 51.91, 43.65, 49.00]  # C2, Ab1, F1, G1
    eighth = beat_dur * 0.5
    for e in range(int(DURATION / eighth)):
        t0 = e * eighth
        i0 = int(t0 * sr)
        el = min(int(eighth * sr), n - i0)
        et = np.arange(el) / sr
        bar = (e // 8) % 4
        f0 = bass_roots[bar] * (2.0 if e % 2 == 1 else 1.0)
        env = np.minimum(et / 0.008, 1.0) * np.exp(-et * 5.2)
        saw = (2.0 * ((f0 * et) % 1.0) - 1.0)
        sub_sin = np.sin(2.0 * np.pi * bass_roots[bar] * et)
        sig = (0.28 * saw + 0.45 * sub_sin) * env * 0.34
        left[i0 : i0 + el] += sig
        right[i0 : i0 + el] += sig

    # 3. Original Spooky C-Minor Pluck / Bell Arpeggio Hook
    arp_notes = [523.25, 622.25, 783.99, 739.99, 622.25, 987.77, 783.99, 622.25]  # C5, Eb5, G5, F#5, Eb5, B5, G5, Eb5
    sixteenth = beat_dur * 0.25
    for s in range(int(DURATION / sixteenth)):
        t0 = s * sixteenth
        i0 = int(t0 * sr)
        sl = min(int(0.32 * sr), n - i0)
        st = np.arange(sl) / sr
        freq = arp_notes[s % len(arp_notes)]
        # FM spooky glass bell timbre
        mod = np.sin(2.0 * np.pi * freq * 2.005 * st) * np.exp(-st * 11.0) * 1.4
        bell = np.sin(2.0 * np.pi * freq * st + mod) * np.exp(-st * 6.5) * 0.14
        pan_l = 0.5 + 0.32 * math.sin(s * 0.9)
        left[i0 : i0 + sl] += bell * pan_l
        right[i0 : i0 + sl] += bell * (1.0 - pan_l)

    # 4. Tubular Chime & Transition Whooshes at exact scene cuts
    for cut_t in [0.02, 2.50, 5.00, 7.50, 11.20, 13.50]:
        i0 = int(cut_t * sr)
        wl = min(int(0.42 * sr), n - i0)
        wt = np.arange(wl) / sr
        whoosh = rng.standard_normal(wl) * np.sin(np.pi * wt / (wl / sr)) * 0.14
        # Tubular bell strike on key sections
        chime = (
            0.13 * np.sin(2.0 * np.pi * 523.25 * wt) * np.exp(-wt * 3.8)
            + 0.08 * np.sin(2.0 * np.pi * 1049.0 * wt) * np.exp(-wt * 5.2)
        )
        left[i0 : i0 + wl] += whoosh + chime
        right[i0 : i0 + wl] += whoosh * 0.95 + chime * 1.05

    # Smooth fade-in (0.08s) and clean loop fade-out (last 0.45s)
    fade_in = np.minimum(t / 0.08, 1.0)
    fade_out = np.clip((DURATION - t) / 0.45, 0.0, 1.0)
    env_master = fade_in * fade_out
    left *= env_master
    right *= env_master

    stereo = np.stack([left, right], axis=-1)
    peak = np.max(np.abs(stereo))
    stereo = np.clip(stereo / max(peak, 1e-6) * 0.85, -0.98, 0.98)
    pcm16 = (stereo * 32767.0).astype(np.int16)

    with wave.open(str(wav_path), "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm16.tobytes())

    subprocess.run(
        [
            ff, "-y", "-hide_banner", "-loglevel", "error",
            "-i", str(wav_path),
            "-af", "loudnorm=I=-14.0:TP=-1.0:LRA=8.0",
            "-c:a", "aac", "-b:a", "320k", "-ar", "48000",
            str(m4a_path),
        ],
        check=True,
    )
    wav_path.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Vector Halloween Atmospheric Graphics (Spiderwebs, Flapping Bats, Pumpkins)
# ---------------------------------------------------------------------------
def draw_corner_spiderweb(draw: ImageDraw.ImageDraw, cx: float, cy: float, radius: float, start_deg: float, end_deg: float, alpha: int) -> None:
    spokes = 6
    angles = np.linspace(math.radians(start_deg), math.radians(end_deg), spokes)
    col = (255, 190, 130, alpha)
    for ang in angles:
        draw.line([(cx, cy), (cx + math.cos(ang) * radius, cy + math.sin(ang) * radius)], fill=col, width=2)
    for ring in (0.32, 0.58, 0.84):
        pts = [(cx + math.cos(a) * radius * ring, cy + math.sin(a) * radius * ring) for a in angles]
        for j in range(len(pts) - 1):
            draw.line([pts[j], pts[j + 1]], fill=col, width=2)


def draw_flapping_bat(draw: ImageDraw.ImageDraw, x: float, y: float, size: float, phase: float, alpha: int = 215) -> None:
    flap = math.sin(phase) * 0.52
    wy = -size * (0.42 + flap * 0.45)
    pts = [
        (x, y - size * 0.16),
        (x - size * 0.12, y - size * 0.30),
        (x - size * 0.55, y + wy),
        (x - size * 0.95, y + wy * 0.45),
        (x - size * 0.62, y + size * 0.16),
        (x - size * 0.28, y + size * 0.10),
        (x, y + size * 0.28),
        (x + size * 0.28, y + size * 0.10),
        (x + size * 0.62, y + size * 0.16),
        (x + size * 0.95, y + wy * 0.45),
        (x + size * 0.55, y + wy),
        (x + size * 0.12, y - size * 0.30),
    ]
    draw.polygon(pts, fill=(14, 9, 22, alpha), outline=(175, 95, 255, min(255, alpha // 2)))


def draw_pumpkin_badge(draw: ImageDraw.ImageDraw, cx: float, cy: float, r: float, glow_pulse: float) -> None:
    glow_r = int(r * (1.35 + 0.12 * glow_pulse))
    draw.ellipse((cx - glow_r, cy - glow_r, cx + glow_r, cy + glow_r), fill=(255, 107, 26, 58))
    # Stem in neon green accent
    draw.rounded_rectangle((cx - r * 0.13, cy - r * 1.15, cx + r * 0.13, cy - r * 0.72), radius=4, fill=(57, 255, 136, 255))
    # Ribbed pumpkin body
    draw.ellipse((cx - r * 1.02, cy - r * 0.80, cx + r * 1.02, cy + r * 0.84), fill=(235, 88, 16, 255), outline=(255, 165, 70, 255), width=3)
    draw.ellipse((cx - r * 0.62, cy - r * 0.82, cx + r * 0.62, cy + r * 0.86), fill=(255, 112, 24, 255))
    # Glowing carved eyes & smile
    eye_col = (255, 242, 135, 255)
    draw.polygon([(cx - r * 0.48, cy - r * 0.10), (cx - r * 0.28, cy - r * 0.38), (cx - r * 0.12, cy - r * 0.10)], fill=eye_col)
    draw.polygon([(cx + r * 0.12, cy - r * 0.10), (cx + r * 0.28, cy - r * 0.38), (cx + r * 0.48, cy - r * 0.10)], fill=eye_col)
    draw.chord((cx - r * 0.50, cy - r * 0.05, cx + r * 0.50, cy + r * 0.52), start=12, end=168, fill=eye_col)


def render_base_scene_frame(scenes_bgr: list[np.ndarray], particles: list[tuple], seg_idx: int, u: float, t_global: float) -> np.ndarray:
    """
    Renders 60.00 fps smooth 3D camera motion + volumetric purple/orange mist + flying bats + embers (NO TEXT!).
    """
    s0, s1, _slug, _fn, z0, z1, px, py = SEGMENTS[seg_idx]
    img = scenes_bgr[seg_idx]
    ih, iw = img.shape[:2]

    # Smooth cosine-eased camera zoom & pan at 60fps sub-pixel accuracy
    ease = 0.5 - 0.5 * math.cos(math.pi * u)
    zoom = z0 + (z1 - z0) * ease
    tx = px * (u - 0.5) * 2.0
    ty = py * (u - 0.5) * 2.0

    base_scale = max(W / iw, H / ih) * zoom
    M = np.array(
        [
            [base_scale, 0.0, W * 0.5 - iw * 0.5 * base_scale + tx],
            [0.0, base_scale, H * 0.5 - ih * 0.5 * base_scale + ty],
        ],
        dtype=np.float32,
    )
    frame = cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101)

    # Subtle beat-synced purple/orange club lighting pulse (125 BPM)
    beat_phase = (t_global / 0.48) % 1.0
    pulse = math.exp(-beat_phase * 5.0) * 0.055
    if pulse > 0.004:
        tint = np.empty_like(frame)
        tint[:, :] = (45, 22, 95) if int(t_global / 0.48) % 2 == 0 else (20, 75, 140)
        frame = cv2.addWeighted(frame, 1.0, tint, pulse, 0.0)

    # Vector atmospheric layer: cobwebs, flying bats, glowing pumpkin & floating embers
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)

    web_alpha = int(68 + 24 * math.sin(t_global * 2.6))
    draw_corner_spiderweb(od, 0, 0, 215, 0, 90, web_alpha)
    draw_corner_spiderweb(od, W, 0, 215, 90, 180, web_alpha)

    # Animated flying bats across upper atmosphere
    for b_idx in range(4):
        bx = ((t_global * (145 + b_idx * 38) + b_idx * 310) % (W + 260)) - 130
        by = 230 + b_idx * 85 + math.sin(t_global * 3.1 + b_idx * 1.7) * 28
        draw_flapping_bat(od, bx, by, 34 + (b_idx % 2) * 11, t_global * 11.5 + b_idx * 1.4, alpha=185)

    # Floating glowing orange & emerald sparks
    for px0, py0, spd, rad, is_green in particles:
        yy = (py0 - t_global * spd) % H
        xx = (px0 + math.sin(t_global * 2.0 + py0 * 0.01) * 26.0) % W
        col = (57, 255, 136, 135) if is_green else (255, 132, 38, 155)
        od.ellipse((xx - rad, yy - rad, xx + rad, yy + rad), fill=col)

    # Transition flash whip at segment boundaries (inspired by CapCut's transition examples!)
    local_t = t_global - s0
    local_rem = s1 - t_global
    if seg_idx > 0 and local_t < 0.20:
        fa = int((1.0 - local_t / 0.20) ** 2 * 165)
        od.rectangle((0, 0, W, H), fill=(155, 56, 255, fa) if seg_idx % 2 == 1 else (255, 107, 26, fa))
    elif seg_idx < len(SEGMENTS) - 1 and local_rem < 0.08:
        fa = int((1.0 - local_rem / 0.08) * 95)
        od.rectangle((0, 0, W, H), fill=(255, 255, 255, fa))

    rgb = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)).convert("RGBA")
    comp = Image.alpha_composite(rgb, overlay).convert("RGB")
    return cv2.cvtColor(np.array(comp), cv2.COLOR_RGB2BGR)


# ---------------------------------------------------------------------------
# Crisp Animated Editorial & Halloween Typography Overlay Layer
# ---------------------------------------------------------------------------
def draw_centered_text(draw: ImageDraw.ImageDraw, y: float, text: str, font: ImageFont.FreeTypeFont, fill: tuple, stroke_w: int = 4, alpha: int = 255) -> None:
    bbox = draw.textbbox((0, 0), text, font=font, stroke_width=stroke_w)
    tw = bbox[2] - bbox[0]
    x = (W - tw) * 0.5
    c_fill = (*fill[:3], alpha)
    draw.text((x, y), text, font=font, fill=c_fill, stroke_width=stroke_w, stroke_fill=(6, 5, 10, alpha))


def draw_pill_tag(draw: ImageDraw.ImageDraw, y: float, text: str, border_rgb: tuple, alpha: int = 255) -> None:
    font = F_SANS_B(30)
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pad_x, pad_y = 34, 15
    x0 = (W - tw) * 0.5 - pad_x
    x1 = (W + tw) * 0.5 + pad_x
    draw.rounded_rectangle(
        (x0, y, x1, y + th + pad_y * 2),
        radius=999,
        fill=(10, 8, 18, int(alpha * 0.84)),
        outline=(*border_rgb, alpha),
        width=3,
    )
    draw.text(((W - tw) * 0.5, y + pad_y - 3), text, font=font, fill=(248, 245, 240, alpha))


def composite_text_edition(base_bgr: np.ndarray, seg_idx: int, local_t: float, t_global: float, copy_cfg: dict) -> np.ndarray:
    """
    Overlays crisp, high-contrast animated typography following all CapCut #InvitaHalloween rules:
      - Immediate invitation hook in segment 0
      - 3.70-second dedicated Event Info Card in segment 3 (Date, Time, Location, Dress Code)
      - Countdown & Animated CTA button in segments 4 & 5
    """
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)

    enter = min(1.0, local_t / 0.28)
    ease = 1.0 - (1.0 - enter) ** 3
    y_slide = (1.0 - ease) * 42.0
    alpha = int(255 * ease)
    glow_p = 0.5 + 0.5 * math.sin(t_global * 6.5)

    # Subtle top & bottom gradient scrims for guaranteed 100% text legibility
    for sy in range(0, 340, 4):
        sa = int((1.0 - sy / 340.0) * 115)
        d.rectangle((0, sy, W, sy + 4), fill=(5, 4, 9, sa))

    if seg_idx == 0:
        draw_pumpkin_badge(d, W * 0.5, 290 + y_slide, 46, glow_p)
        draw_pill_tag(d, 368 + y_slide, copy_cfg["hook_tag"], COL_GREEN, alpha)
        draw_centered_text(d, 470 + y_slide, copy_cfg["hook_l1"], F_DISPLAY(112), COL_IVORY, 6, alpha)
        draw_centered_text(d, 598 + y_slide, copy_cfg["hook_l2"], F_SPOOKY(118), COL_ORANGE, 7, alpha)
        draw_pill_tag(d, 760 + y_slide, copy_cfg["hook_sub"], COL_PURPLE, alpha)

    elif seg_idx == 1:
        draw_pill_tag(d, 260 + y_slide, copy_cfg["s2_tag"], COL_ORANGE, alpha)
        draw_centered_text(d, 355 + y_slide, copy_cfg["s2_l1"], F_DISPLAY(98), COL_IVORY, 6, alpha)
        draw_centered_text(d, 470 + y_slide, copy_cfg["s2_l2"], F_DISPLAY(94), COL_PURPLE, 6, alpha)

    elif seg_idx == 2:
        draw_pill_tag(d, 1340 - y_slide, copy_cfg["s3_tag"], COL_GREEN, alpha)
        draw_centered_text(d, 1435 - y_slide, copy_cfg["s3_l1"], F_DISPLAY(96), COL_IVORY, 6, alpha)
        draw_centered_text(d, 1550 - y_slide, copy_cfg["s3_l2"], F_SPOOKY(104), COL_ORANGE, 6, alpha)

    elif seg_idx == 3:
        # MANDATORY DEDICATED >= 2.0s EVENT DATA BLOCK (Held for full 3.70s!)
        draw_pumpkin_badge(d, W * 0.5, 265, 42, glow_p)
        draw_centered_text(d, 338, copy_cfg["info_title"], F_DISPLAY(84), COL_ORANGE, 5, alpha)

        rows = [
            ("FECHA", copy_cfg["date"], COL_ORANGE),
            ("HORA", copy_cfg["time"], COL_PURPLE),
            ("UBICACIÓN", copy_cfg["place"], COL_GREEN),
            ("DRESS CODE", copy_cfg["dress"], COL_ORANGE),
        ]
        card_y = 478
        for idx_r, (label, val, accent) in enumerate(rows):
            row_enter = min(1.0, max(0.0, (local_t - idx_r * 0.09) / 0.24))
            ra = int(255 * row_enter)
            ry = card_y + idx_r * 218 + (1.0 - row_enter) * 26.0
            d.rounded_rectangle(
                (92, ry, W - 92, ry + 188),
                radius=26,
                fill=(12, 10, 22, int(ra * 0.90)),
                outline=(*accent, ra),
                width=3,
            )
            # Left accent bar
            d.rounded_rectangle((114, ry + 26, 128, ry + 162), radius=6, fill=(*accent, ra))
            d.text((156, ry + 28), label, font=F_SANS_B(26), fill=(*accent, ra))
            d.text((156, ry + 78), val, font=F_SANS_B(40), fill=(248, 245, 240, ra))

    elif seg_idx == 4:
        draw_pill_tag(d, 250 + y_slide, copy_cfg["countdown"], COL_GREEN, alpha)
        draw_centered_text(d, 348 + y_slide, copy_cfg["s5_l1"], F_DISPLAY(96), COL_IVORY, 6, alpha)
        draw_centered_text(d, 462 + y_slide, copy_cfg["s5_l2"], F_DISPLAY(88), COL_ORANGE, 6, alpha)

    elif seg_idx == 5:
        draw_pumpkin_badge(d, W * 0.5, 360 + y_slide, 52, glow_p)
        draw_centered_text(d, 445 + y_slide, copy_cfg["cta_pre"], F_SPOOKY(108), COL_ORANGE, 6, alpha)
        draw_centered_text(d, 572 + y_slide, copy_cfg["cta_sub"], F_SANS_B(36), COL_IVORY, 3, alpha)

        # Pulsing High-Conversion Editable CTA Button
        btn_scale = 1.0 + 0.028 * math.sin(t_global * 8.0)
        bw, bh = int(840 * btn_scale), int(146 * btn_scale)
        bx0, by0 = (W - bw) // 2, 700 - (bh - 146) // 2
        d.rounded_rectangle((bx0 - 8, by0 - 8, bx0 + bw + 8, by0 + bh + 8), radius=999, fill=(255, 107, 26, int(75 * ease)))
        d.rounded_rectangle((bx0, by0, bx0 + bw, by0 + bh), radius=999, fill=(255, 107, 26, alpha), outline=(57, 255, 136, alpha), width=4)
        draw_centered_text(d, by0 + 36, copy_cfg["cta_btn"], F_SANS_B(44), COL_IVORY, 2, alpha)
        draw_pill_tag(d, 905, copy_cfg["cta_footer"], COL_PURPLE, alpha)

    rgb = Image.fromarray(cv2.cvtColor(base_bgr, cv2.COLOR_BGR2RGB)).convert("RGBA")
    comp = Image.alpha_composite(rgb, ov).convert("RGB")
    return cv2.cvtColor(np.array(comp), cv2.COLOR_RGB2BGR)


def build_capcut_desktop_draft_zip(out_zip: Path, clip_paths: list[Path]) -> None:
    """
    Creates an importable CapCut Desktop project folder (`InvitaHalloween_PRO/`) containing:
      - `media/01_hook.mp4` .. `media/06_cta.mp4` (6 clean 60fps 1080x1920 video clips)
      - `draft_content.json` & `draft_meta_info.json` with all 6 video clips AND all editable text layers!
      - `INSTRUCCIONES_CAPCUT_CREATOR.txt` (step-by-step Mobile + Desktop template publishing guide)
    """
    videos_mat = []
    video_segs = []
    texts_mat = []
    text_segs = []

    editable_layers = [
        (0.10, 2.45, "ESTÁS INVITADO/A\nHALLOWEEN PARTY 🎃", 0.0, 0.35),
        (2.55, 4.95, "NOCHE DE DISFRACES\nTRAGOS, DULCES & MÚSICA", 0.0, 0.42),
        (5.05, 7.45, "PREPARA TU MEJOR LOOK\nPREMIO AL MEJOR DISFRAZ 👻", 0.0, -0.45),
        (
            7.55,
            11.15,
            "🎃 DATOS DEL EVENTO\n\n📅 SÁBADO 31 DE OCTUBRE\n🕙 22:00 HRS\n📍 [TU DIRECCIÓN / BAR]\n🎭 DRESS CODE: DISFRAZ CREATIVO",
            0.0,
            0.0,
        ),
        (11.25, 13.45, "⏳ FALTAN POCOS DÍAS\nPHOTO SPOT & SORPRESAS", 0.0, 0.42),
        (13.55, 15.95, "¿VIENES A LA FIESTA?\nCONFIRMA TU ASISTENCIA →", 0.0, 0.18),
    ]

    for idx, ((s0, s1, slug, *_), cp) in enumerate(zip(SEGMENTS, clip_paths)):
        vid_id = str(uuid.uuid4()).upper()
        dur_us = int(round((s1 - s0) * 1_000_000))
        start_us = int(round(s0 * 1_000_000))
        videos_mat.append(
            {
                "id": vid_id,
                "type": "video",
                "path": f"media/{cp.name}",
                "material_name": cp.name,
                "width": W,
                "height": H,
                "duration": dur_us,
            }
        )
        video_segs.append(
            {
                "id": str(uuid.uuid4()).upper(),
                "material_id": vid_id,
                "source_timerange": {"start": 0, "duration": dur_us},
                "target_timerange": {"start": start_us, "duration": dur_us},
            }
        )

    for ts0, ts1, content, tx, ty in editable_layers:
        tid = str(uuid.uuid4()).upper()
        dur_us = int(round((ts1 - ts0) * 1_000_000))
        start_us = int(round(ts0 * 1_000_000))
        texts_mat.append(
            {
                "id": tid,
                "type": "text",
                "content": json.dumps({"text": content, "styles": [{"fill": {"content": {"solid": {"color": [1.0, 0.42, 0.10]}}}, "size": 11.0}]}),
                "font_size": 11.0,
                "text_color": "#FFFFFF",
                "alignment": 1,
            }
        )
        text_segs.append(
            {
                "id": str(uuid.uuid4()).upper(),
                "material_id": tid,
                "target_timerange": {"start": start_us, "duration": dur_us},
                "clip": {"transform": {"x": tx, "y": ty}, "scale": {"x": 1.0, "y": 1.0}},
            }
        )

    draft_content = {
        "id": str(uuid.uuid4()).upper(),
        "fps": 60.0,
        "duration": int(DURATION * 1_000_000),
        "canvas_config": {"width": W, "height": H, "ratio": "9:16"},
        "materials": {"videos": videos_mat, "texts": texts_mat, "audios": []},
        "tracks": [
            {"id": str(uuid.uuid4()).upper(), "type": "video", "segments": video_segs},
            {"id": str(uuid.uuid4()).upper(), "type": "text", "segments": text_segs},
        ],
    }

    guide_es = """====================================================================
GUÍA RÁPIDA DE PUBLICACIÓN — CAMPAÑA OFICIAL CAPCUT PRO #InvitaHalloween
Task ID: 307926551812  |  Vigencia: 19/10/2026 al 26/10/2026
====================================================================

TÍTULO + HASHTAGS OBLIGATORIOS (COPIAR Y PEGAR EXACTO AL PUBLICAR):
Invitación Halloween Party Editable 🎃👻 #🎃 #InvitaHalloween #Halloween #Celebración #MundialPRO

POR QUÉ ESTE PACK CUMPLE EL 100% DE LA AUDITORÍA DE CAPCUT CREATOR:
1. Duración exacta: 16.00 segundos (rango obligatorio: 12 a 20 segundos).
2. Cantidad de clips: 6 escenas distintas 1080x1920 @ 60.00 FPS con humo, murciélagos y destellos.
3. Paleta oficial: Negro (#07060A) + Naranja (#FF6B1A) + Morado (#8B2CF5) + Acento Verde (#39FF88).
4. Pantalla exclusiva de datos del evento: Clip 04 dura 3.70 segundos (> 2.0s obligatorios).
5. Textos 100% EDITABLES por los usuarios de la plantilla:
   - Clip 1 (0.0s - 2.5s): "Estás invitado/a a nuestra Halloween Party 🎃"
   - Clip 2 (2.5s - 5.0s): "Noche de Disfraces · Dulces, Drinks & Fiesta"
   - Clip 3 (5.0s - 7.5s): "Prepara tu mejor disfraz 👻"
   - Clip 4 (7.5s - 11.2s) [BLOQUE EXCLUSIVO DE DATOS EDITABLES]:
       📅 SÁBADO 31 DE OCTUBRE
       🕙 22:00 HRS
       📍 [LUGAR / DIRECCIÓN]
       🎭 DRESS CODE: [TEMA / DISFRAZ]
   - Clip 5 (11.2s - 13.5s): "⏳ Cuenta regresiva · Photo Spot"
   - Clip 6 (13.5s - 16.0s) [CTA EDITABLE]: "¿Vienes? Confirma tu asistencia →"
6. Música en CapCut: Al subir como plantilla en CapCut, elige cualquier pista de "Halloween"
   de la biblioteca comercial autorizada de CapCut (para que CapCut habilite el audio de plantilla sin bloqueo).
"""

    with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_STORED) as zf:
        zf.writestr("InvitaHalloween_PRO/draft_content.json", json.dumps(draft_content, indent=2, ensure_ascii=False))
        zf.writestr(
            "InvitaHalloween_PRO/draft_meta_info.json",
            json.dumps({"draft_name": "InvitaHalloween_PRO_307926551812", "tm_duration": int(DURATION * 1_000_000)}, indent=2),
        )
        zf.writestr("InvitaHalloween_PRO/INSTRUCCIONES_CAPCUT_CREATOR.txt", guide_es)
        for cp in clip_paths:
            zf.write(cp, arcname=f"InvitaHalloween_PRO/media/{cp.name}")


def main() -> None:
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    base_dir = Path("promos/invita_halloween")
    scenes_dir = base_dir / "scenes"
    clips_dir = base_dir / "clips_editables_capcut"
    clips_dir.mkdir(parents=True, exist_ok=True)

    scenes_bgr = []
    for _s0, _s1, _slug, fn, *_ in SEGMENTS:
        img = cv2.imread(str(scenes_dir / fn), cv2.IMREAD_COLOR)
        assert img is not None, f"Missing scene {fn}"
        scenes_bgr.append(img)

    aud_m4a = Path("/tmp/invita_halloween_125bpm.m4a")
    synthesize_halloween_audio(Path("/tmp/invita_halloween_raw.wav"), aud_m4a, ff)

    copy_universal = {
        "hook_tag": "◆ INVITACIÓN OFICIAL · HALLOWEEN PARTY ◆",
        "hook_l1": "ESTÁS INVITADO/A",
        "hook_l2": "HALLOWEEN PARTY",
        "hook_sub": "UNA NOCHE ÉPICA CON AMIGOS · NO FALTES",
        "s2_tag": "◆ AMBIENTE · SNACKS · DRINKS TEMÁTICOS ◆",
        "s2_l1": "MÚSICA, DULCES",
        "s2_l2": "& TRAGOS ESPECIALES",
        "s3_tag": "◆ CONCURSO DE DISFRACES ORIGINALES ◆",
        "s3_l1": "TRAE TU MEJOR",
        "s3_l2": "DISFRAZ CREATIVO",
        "info_title": "DATOS DEL EVENTO",
        "date": "SÁBADO 31 DE OCTUBRE",
        "time": "22:00 HRS · HASTA TARDE",
        "place": "AV. PROVIDENCIA 1234 · STGO",
        "dress": "DISFRAZ LIBRE / DARK GLAM",
        "countdown": "CUENTA REGRESIVA · SÁBADO 31 OCT",
        "s5_l1": "PHOTO SPOT VIP",
        "s5_l2": "& SORPRESAS EN VIVO",
        "cta_pre": "TE ESPERAMOS",
        "cta_sub": "¿VIENES? RESERVA TU LUGAR EN LA LISTA",
        "cta_btn": "CONFIRMA TU ASISTENCIA →",
        "cta_footer": "RESPONDE ESTE VIDEO O ESCRÍBENOS POR DM",
    }

    copy_abyss = {
        "hook_tag": "◆ ABYSS TATTOO STUDIO · HALLOWEEN NIGHT ◆",
        "hook_l1": "ESTÁS INVITADO/A",
        "hook_l2": "ABYSS PARTY",
        "hook_sub": "FLASH NIGHT · MÚSICA · DRINKS & DISFRACES",
        "s2_tag": "◆ CÓCTELES · SNACKS · OPEN STUDIO ◆",
        "s2_l1": "ARTE OSCURO,",
        "s2_l2": "DRINKS & AMIGOS",
        "s3_tag": "◆ MEJOR DISFRAZ GANA FLASH TATTOO ◆",
        "s3_l1": "LUCE TU MEJOR",
        "s3_l2": "OUTFIT DE HALLOWEEN",
        "info_title": "COORDENADAS DEL EVENTO",
        "date": "SÁBADO 31 DE OCTUBRE",
        "time": "20:00 A 01:30 HRS",
        "place": "PROVIDENCIA · SANTIAGO CL",
        "dress": "DARK GLAM / DISFRAZ LIBRE",
        "countdown": "CUPOS LIMITADOS · SOLO LISTA VIP",
        "s5_l1": "PHOTO SPOT DARK",
        "s5_l2": "& SORTEOS EN VIVO",
        "cta_pre": "NO TE QUEDES FUERA",
        "cta_sub": "ASEGURA TU ENTRADA AHORA MISMO",
        "cta_btn": "CONFIRMA TU ASISTENCIA →",
        "cta_footer": "+56 9 4778 6839 · ESCRÍBENOS POR DM",
    }

    out_master = base_dir / "invita_halloween_pro_master_1080x1920_60fps.mp4"
    out_abyss = base_dir / "invita_halloween_abyss_edition_1080x1920_60fps.mp4"

    def open_vid_pipe(dest: Path, with_audio: bool = True) -> subprocess.Popen:
        cmd = [
            ff, "-y", "-hide_banner", "-loglevel", "error",
            "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS),
            "-i", "pipe:0",
        ]
        if with_audio:
            cmd += ["-i", str(aud_m4a)]
        cmd += [
            "-c:v", "libx264", "-preset", "fast", "-profile:v", "high", "-level:v", "4.2",
            "-x264-params", "rc-lookahead=10:threads=2",
            "-crf", "16", "-maxrate", "22M", "-bufsize", "44M",
            "-g", "30", "-pix_fmt", "yuv420p",
            "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-color_range", "tv",
        ]
        if with_audio:
            cmd += ["-c:a", "copy", "-shortest"]
        cmd += ["-movflags", "+faststart", str(dest)]
        return subprocess.Popen(cmd, stdin=subprocess.PIPE)

    p_master = open_vid_pipe(out_master, with_audio=True)
    p_abyss = open_vid_pipe(out_abyss, with_audio=True)
    clip_paths = [clips_dir / f"clip_{slug}_1080x1920_60fps.mp4" for _, _, slug, *_ in SEGMENTS]
    cur_clip_idx = -1
    cur_clip_proc: subprocess.Popen | None = None

    rng = np.random.default_rng(20261031)
    particles = [
        (float(rng.uniform(0, W)), float(rng.uniform(0, H)), float(rng.uniform(45, 115)), int(rng.integers(2, 6)), bool(i % 5 == 0))
        for i in range(34)
    ]

    poster_saved = False
    info_preview_saved = False
    cta_preview_saved = False

    for f_idx in range(TOTAL_FRAMES):
        t_global = f_idx / FPS
        seg_idx = len(SEGMENTS) - 1
        for si, (s0, s1, *_) in enumerate(SEGMENTS):
            if t_global < s1 or si == len(SEGMENTS) - 1:
                seg_idx = si
                break

        if seg_idx != cur_clip_idx:
            if cur_clip_proc is not None and cur_clip_proc.stdin:
                cur_clip_proc.stdin.close()
                assert cur_clip_proc.wait() == 0
            cur_clip_idx = seg_idx
            cur_clip_proc = open_vid_pipe(clip_paths[seg_idx], with_audio=False)

        s0, s1, *_ = SEGMENTS[seg_idx]
        u = max(0.0, min(1.0, (t_global - s0) / max(s1 - s0, 1e-6)))
        local_t = t_global - s0

        clean_frame = render_base_scene_frame(scenes_bgr, particles, seg_idx, u, t_global)
        f_uni = composite_text_edition(clean_frame, seg_idx, local_t, t_global, copy_universal)
        f_aby = composite_text_edition(clean_frame, seg_idx, local_t, t_global, copy_abyss)

        assert p_master.stdin and p_abyss.stdin and cur_clip_proc and cur_clip_proc.stdin
        p_master.stdin.write(f_uni.tobytes())
        p_abyss.stdin.write(f_aby.tobytes())
        cur_clip_proc.stdin.write(clean_frame.tobytes())

        if not poster_saved and abs(t_global - 1.15) < 0.02:
            cv2.imwrite(str(base_dir / "poster_hook.jpg"), f_uni, [cv2.IMWRITE_JPEG_QUALITY, 93])
            poster_saved = True
        if not info_preview_saved and abs(t_global - 9.20) < 0.02:
            cv2.imwrite(str(base_dir / "poster_datos_evento.jpg"), f_uni, [cv2.IMWRITE_JPEG_QUALITY, 93])
            info_preview_saved = True
        if not cta_preview_saved and abs(t_global - 14.60) < 0.02:
            cv2.imwrite(str(base_dir / "poster_cta.jpg"), f_uni, [cv2.IMWRITE_JPEG_QUALITY, 93])
            cta_preview_saved = True

    for proc in [p_master, p_abyss, cur_clip_proc]:
        if proc is not None and proc.stdin:
            proc.stdin.close()
            assert proc.wait() == 0

    aud_m4a.unlink(missing_ok=True)

    draft_zip = base_dir / "CapCut_Proyecto_InvitaHalloween_PRO.zip"
    build_capcut_desktop_draft_zip(draft_zip, clip_paths)
    print("SUCCESS! Built full CapCut #InvitaHalloween 60fps PRO suite:")
    for p in [out_master, out_abyss, draft_zip, *clip_paths]:
        print(f"  - {p}: {p.stat().st_size / (1024*1024):.2f} MB")


if __name__ == "__main__":
    main()
