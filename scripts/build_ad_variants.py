#!/usr/bin/env python3
"""
build_ad_variants.py — Genera el pack publicitario complementario desde el mismo pipeline maestro:
  1) Variante B (A/B Testing Local Meta Ads, 9:16 · 1080x1920 · 60 fps):
       Arranca con Vuelo Aéreo FPV Dron sobre San Bernardo + Fachada Real José Joaquín Pérez 528 (0.00-2.40s)
       -> Macro Aguja + Hombro Chiaroscuro (2.40-4.50s) -> empalme continuo con el bloque central y CTA (4.50-15.00s).
  2) Adaptación Nativa 4:5 Feed Instagram / Meta Ads (1080x1350 · 30 fps · 15.00s):
       Reencuadre óptico real desde las placas overscan 1296x2304 (sin recortar textos ni HUD) con Packshot 4:5 dedicado.
"""

import math
import os
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw

ROOT = "/home/user/abysstattoo"
sys.path.insert(0, os.path.join(ROOT, "scripts"))
os.chdir(ROOT)

import build_reel_commercial as M  # noqa: E402
import reel_kit as K  # noqa: E402

OUT_HOOK_B = "film/reel_comercial_abyss_15s_hook_b_local_60fps.mp4"
COVER_HOOK_B = "film/reel_comercial_abyss_15s_cover_hook_b.jpg"

OUT_FEED_4X5 = "film/reel_comercial_abyss_15s_1080x1350_4x5_feed.mp4"
POSTER_4X5 = "film/reel_comercial_abyss_15s_4x5_poster.jpg"


# ==============================================================================
# 1. VARIANTE B — HOOK LOCAL SAN BERNARDO (9:16 · 1080x1920 · 60 FPS)
# ==============================================================================
SHOTS_HOOK_B = [
    # 01B — HOOK LOCAL: Vuelo Dron FPV San Bernardo desde el fotograma 0
    dict(
        t0=0.00, t1=1.20, kind="single",
        plate="plate_v03_dron_aereo.mp4", speed=1.95, offset=0.05,
        cam=K.Camera(z=(1.02, 1.30), c=((0.50, 0.47), (0.50, 0.54)), ease="in", tilt=((0.0, 0.0), (0.0, -1.8))),
        lens="DRON FPV · SAN BERNARDO 16mm",
        scrim="hero",
        zoom_blur_head=0.40,
        flash_head=(0.22, K.PAPER),
        callout=K.callout_badge("SAN BERNARDO", "JOSÉ JOAQUÍN PÉREZ 528"),
        lines=K.stack([
            ("EN SAN BERNARDO", "mont700", 27, K.TEAL_L, 9, 0.05, "rise", "label"),
            ("HAY OTRO NIVEL.", "cinzel800", 78, K.PAPER, 4, 0.20, "punch", "display"),
        ], top=1190, block_gap=0.38),
    ),
    # 02B — FACHADA VERIFICADA 528
    dict(
        t0=1.20, t1=2.40, kind="single",
        plate="plate_p01_fachada_real.jpg",
        cam=K.Camera(z=(1.05, 1.22), c=((0.49, 0.52), (0.54, 0.45)), ease="out", tilt=((1.4, 1.6), (0.0, 0.0))),
        lens="FACHADA REAL · 24mm",
        scrim="lower",
        zoom_blur_head=0.32,
        lines=K.stack([
            ("JOSÉ JOAQUÍN PÉREZ 528", "cinzel800", 54, K.PAPER, 3, 0.06, "punch", "display"),
            ("ABYSS TATTOO STUDIO  ·  DESDE 2009", "mont600", 22, K.CREAM, 6, 0.24, "rise", "label"),
        ], top=1215, block_gap=0.46),
    ),
    # 03B — ECU MACRO AGUJA EN VIVO
    dict(
        t0=2.40, t1=3.60, kind="single",
        plate="plate_v01_macro_aguja.mp4", speed=1.18, offset=0.02,
        cam=K.Camera(z=(1.36, 1.12), c=((0.50, 0.44), (0.50, 0.49)), ease="out", rot=(1.6, 0.0), shake=0.30, seed=1),
        lens="ECU MACRO · 100mm",
        scrim="lower",
        whip=("x", 22),
        lines=K.stack([
            ("PRECISIÓN DE AUTOR", "cinzel800", 66, K.PAPER, 4, 0.06, "punch", "display"),
            ("CADA LÍNEA ES UNA FIRMA", "mont600", 22, K.TEAL_L, 7, 0.22, "rise", "label"),
        ], top=1215, block_gap=0.46),
    ),
    # 04B — PRIMER PLANO CHIAROSCURO
    dict(
        t0=3.60, t1=4.50, kind="single",
        plate="plate_v02_hero_reveal.mp4", speed=1.08, offset=0.05,
        cam=K.Camera(z=(1.05, 1.23), c=((0.48, 0.43), (0.50, 0.41)), ease="ramp", rot=(-1.2, 0.4)),
        lens="PRIMER PLANO · 50mm",
        scrim="lower",
        flash_head=(0.14, K.CREAM),
        lines=K.stack([
            ("ARTE EN LA PIEL", "cinzel800", 72, K.PAPER, 4, 0.06, "punch", "display"),
            ("DISEÑO 100 % PERSONALIZADO", "mont600", 21, K.CREAM, 6, 0.20, "rise", "label"),
        ], top=1215, block_gap=0.46),
    ),
]


def build_hook_b():
    print("=== GENERANDO VARIANTE B (HOOK LOCAL 528 · 1080x1920 · 60 FPS) ===")
    saved_shots = list(M.SHOTS)
    M.SHOTS[:] = SHOTS_HOOK_B + saved_shots[4:]

    cap_master = cv2.VideoCapture(M.OUT_SOCIAL)
    log_f = open("/tmp/ff_hook_b.log", "wb")
    cmd = [
        M.FFMPEG, "-y",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1080x1920", "-r", "60",
        "-i", "-",
        "-i", M.AUDIO,
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-maxrate", "16M", "-bufsize", "32M",
        "-profile:v", "high", "-level", "4.2",
        "-pix_fmt", "yuv420p",
        "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        "-movflags", "+faststart", "-shortest",
        OUT_HOOK_B,
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=log_f)
    cap_master.set(cv2.CAP_PROP_POS_FRAMES, 270)
    for i in range(900):
        if i < 270:
            fr = M.render_frame(i)
            if i == 35:
                Image.fromarray(fr).save(COVER_HOOK_B, quality=94)
        else:
            ok, bgr = cap_master.read()
            fr = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB) if ok else M.render_frame(i)
        proc.stdin.write(fr.tobytes())
        if (i + 1) % 300 == 0:
            print(f"  [Hook B] {i + 1}/900 frames", flush=True)
    cap_master.release()
    proc.stdin.close()
    rc = proc.wait()
    log_f.close()
    M.SHOTS[:] = saved_shots
    if rc != 0:
        raise RuntimeError(open("/tmp/ff_hook_b.log", "rb").read().decode(errors="ignore")[-1500:])
    print(f"Variante Hook B lista -> {OUT_HOOK_B}")


# ==============================================================================
# 2. ADAPTACIÓN NATIVA 4:5 FEED INSTAGRAM / META ADS (1080x1350 · 30 FPS)
# ==============================================================================
FW, FH = 1080, 1350
FPS_FEED = 30
N_FEED = int(round(M.DUR * FPS_FEED))  # 450 frames exactos


def corner_hud_4x5(alpha: int = 126) -> np.ndarray:
    img = Image.new("RGBA", (FW, FH), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    x0, y0, x1, y1 = 56, 66, 1024, 1284
    length = 42
    for (cx, cy, sx, sy) in [(x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)]:
        K.line_alpha(d, [(cx, cy), (cx + sx * length, cy)], K.BONE, 2, alpha)
        K.line_alpha(d, [(cx, cy), (cx, cy + sy * length)], K.BONE, 2, alpha)
    return np.array(img)


HUD4 = corner_hud_4x5(126)
HUD4_SOFT = corner_hud_4x5(64)

ys4 = np.linspace(0.0, 1.0, FH, dtype=np.float32)
SCRIM4_LOWER = np.clip(
    ((1.0 - 0.26 * np.exp(-((ys4 - 0.06) ** 2) / 0.012)) * (1.0 - 0.76 * (np.clip((ys4 - 0.50) / 0.44, 0.0, 1.0) ** 1.45))) * 256.0,
    0,
    256,
).astype(np.uint16)[:, None, None]

yy4, xx4 = np.mgrid[0:FH, 0:FW].astype(np.float32)
r4 = np.sqrt(((xx4 - FW / 2.0) / (FW / 2.0)) ** 2 * 0.85 + ((yy4 - FH / 2.0) / (FH / 2.0)) ** 2)
VIG4 = np.clip((1.0 - np.clip(r4, 0.0, 1.6) ** 2.25 * 0.34) * 256.0, 0, 256).astype(np.uint16)[..., None]
GRAINS4 = [np.random.default_rng(19 + k).normal(0.0, 1.7, (FH, FW, 1)).astype(np.int16) for k in range(6)]

EMBLEM4 = K.load_rgba(M.plate_path("emblema_abyss_alpha.png"), (246, 246))
GLOW4 = K.glow(390, K.TEAL, 80.0)
RINGS4 = K.concentric_rings(620, rings=7, color=K.BONE, max_alpha=28)


def shift_lines_for_4x5(lines, delta_y: float = -295.0):
    return [(img, cx, cy + delta_y, t0, style) for (img, cx, cy, t0, style) in lines]


def hud_overlay_4x5(canvas: np.ndarray, t: float, lens: str, soft: bool = False):
    K.paste_rgba(canvas, HUD4_SOFT if soft else HUD4, 0, 0, 1.0)
    K.paste_rgba(canvas, M.BRAND_TOP, 540 - M.BRAND_TOP.shape[1] // 2, 28, 0.72 if soft else 0.90)
    if not soft:
        y = 56
        x0, x1 = 56, 1024
        xp = int(round(x0 + (x1 - x0) * K.clamp01(t / M.DUR)))
        canvas[y : y + 2, x0:x1] = (canvas[y : y + 2, x0:x1].astype(np.uint16) * 180 >> 8).astype(np.uint8) + 22
        canvas[y : y + 3, x0:xp] = np.array(K.TEAL_L, dtype=np.uint8)
        blink = 0.35 + 0.65 * (0.5 + 0.5 * math.sin(t * 2 * math.pi * 1.25))
        im_dot = Image.new("RGBA", (14, 14), (0, 0, 0, 0))
        ImageDraw.Draw(im_dot).ellipse((1, 1, 13, 13), fill=(214, 72, 62, int(255 * blink)))
        K.paste_rgba(canvas, np.array(im_dot), 82, 92, 1.0)
        K.paste_rgba(canvas, M.REC_TAG, 102, 82, 0.90)
        lt = M.lens_tag(lens)
        K.paste_rgba(canvas, lt, 1010 - lt.shape[1], 83, 0.88)


def render_cta_4x5(local_t: float, dur: float) -> np.ndarray:
    p = local_t / dur
    z, cx, cy, *_ = K.Camera(z=(1.04, 1.12), c=((0.50, 0.48), (0.50, 0.46)), ease="out").state(p)
    canvas = K.render_camera(M.CTA_BG_BASE, z, cx, cy, out_w=FW, out_h=FH)

    g_alpha = 0.72 + 0.18 * math.sin(local_t * 2.2)
    K.paste_rgba(canvas, GLOW4, y=276 - GLOW4.shape[0] // 2, alpha=g_alpha * K.clamp01(local_t / 0.35))
    K.paste_rgba(canvas, RINGS4, y=276 - RINGS4.shape[0] // 2, alpha=0.85 * K.clamp01(local_t / 0.5))

    tin = K.clamp01(local_t / 0.42)
    sc = 0.85 + 0.15 * K.ease_out_back(tin, 1.35)
    ew, eh = max(2, int(round(EMBLEM4.shape[1] * sc))), max(2, int(round(EMBLEM4.shape[0] * sc)))
    emb = cv2.resize(EMBLEM4, (ew, eh), interpolation=cv2.INTER_LINEAR)
    K.paste_rgba(canvas, emb, 540 - ew // 2, 276 - eh // 2, K.ease_out_cubic(tin))

    M.draw_line(canvas, M.CTA_TITLE, 540, 488, local_t, 0.16, dur, "punch")
    M.draw_line(canvas, M.CTA_SUB, 540, 566, local_t, 0.30, dur, "hold")
    K.paste_rgba(canvas, M.CTA_DIV, 540 - M.CTA_DIV.shape[1] // 2, 622 - M.CTA_DIV.shape[0] // 2, K.clamp01((local_t - 0.42) / 0.26))

    if local_t >= 0.52:
        bt = K.clamp01((local_t - 0.52) / 0.30)
        bsc = 0.88 + 0.12 * K.ease_out_back(bt, 1.55)
        bw, bh = max(2, int(round(M.CTA_PILL.shape[1] * bsc))), max(2, int(round(M.CTA_PILL.shape[0] * bsc)))
        pill_im = cv2.resize(M.CTA_PILL, (bw, bh), interpolation=cv2.INTER_LINEAR)
        shimmer_p = (local_t - 0.80) / 0.85 if 0.80 <= local_t <= 1.65 else -1.0
        K.paste_rgba_shimmer(canvas, pill_im, 540, 718, K.ease_out_cubic(bt), shimmer_p)

    M.draw_line(canvas, M.CTA_HANDLE, 540, 830, local_t, 0.72, dur, "hold")
    M.draw_line(canvas, M.CTA_ADDR, 540, 904, local_t, 0.82, dur, "hold")
    M.draw_line(canvas, M.CTA_HOURS, 540, 978, local_t, 0.92, dur, "hold")

    if local_t < 0.16:
        canvas = K.flash_frame(canvas, 0.30 * (1.0 - local_t / 0.16) ** 2.0, K.PAPER)
    hud_overlay_4x5(canvas, 12.60 + local_t, "ABYSS · J. J. PÉREZ 528", soft=True)
    if dur - local_t < 0.20:
        canvas = K.flash_frame(canvas, 0.45 * (1.0 - (dur - local_t) / 0.20) ** 2.0, K.OBSIDIAN)
    return canvas


def render_frame_4x5(idx: int) -> np.ndarray:
    t = idx / FPS_FEED
    sh = M.shot_at(t)
    local_t = t - sh["t0"]
    dur = sh["t1"] - sh["t0"]
    p = local_t / dur
    kind = sh["kind"]

    if kind == "cta":
        c = render_cta_4x5(local_t, dur)
        return K.finish_fast(c, VIG4, GRAINS4[idx % len(GRAINS4)])

    if kind == "split":
        canvas = np.zeros((FH, FW, 3), dtype=np.uint8)
        b_top, b_bot = 590, 760
        zt, cxt, cyt, rott, txt, tyt = sh["top_cam"].state(p)
        zb, cxb, cyb, rotb, txb, tyb = sh["bot_cam"].state(p)
        canvas[:b_top] = K.render_camera(M.sample_plate(sh["top_plate"], local_t), zt * 0.94, cxt, cyt, rott, txt, tyt, out_w=FW, out_h=b_top)
        canvas[b_bot:] = K.render_camera(M.sample_plate(sh["bot_plate"], local_t), zb * 0.94, cxb, cyb, rotb, txb, tyb, out_w=FW, out_h=FH - b_bot)
        canvas[b_top:b_bot] = np.array(K.OBSIDIAN, dtype=np.uint8)
        im = Image.fromarray(canvas)
        d = ImageDraw.Draw(im)
        d.line([(0, b_top), (FW, b_top)], fill=K.BONE, width=3)
        d.line([(0, b_bot), (FW, b_bot)], fill=K.BONE, width=3)
        K.diamond(d, 86, (b_top + b_bot) // 2, 8, K.TEAL_L, 255)
        K.diamond(d, FW - 86, (b_top + b_bot) // 2, 8, K.TEAL_L, 255)
        canvas = np.array(im)
        lines = shift_lines_for_4x5(sh.get("lines", []), -282.0)
    else:
        if kind == "dual_cut":
            sp = sh["split_at"]
            if local_t < sp:
                src = M.sample_plate(sh["plate_a"], local_t)
                z, cx, cy, rot, tx, ty = sh["cam_a"].state(local_t / sp)
            else:
                src = M.sample_plate(sh["plate_b"], local_t - sp)
                z, cx, cy, rot, tx, ty = sh["cam_b"].state((local_t - sp) / (dur - sp))
        else:
            src = M.sample_plate(sh["plate"], local_t, sh.get("speed", 1.0), sh.get("offset", 0.0))
            z, cx, cy, rot, tx, ty = sh["cam"].state(p)
        # En 4:5 ampliamos ligeramente el ángulo de visión (z * 0.94) para encuadre editorial cómodo
        canvas = K.render_camera(src, z * 0.94, cx, cy, rot, tx, ty, out_w=FW, out_h=FH)
        if kind == "dual_cut" and abs(local_t - sh["split_at"]) < 0.09:
            canvas = K.flash_frame(canvas, 0.22 * (1.0 - abs(local_t - sh["split_at"]) / 0.09) ** 2.0, K.CREAM)
        lines = shift_lines_for_4x5(sh.get("lines", []), -295.0)

    if "whip" in sh:
        axis, amt = sh["whip"]
        w_env = M.whip_envelope(local_t, dur)
        if w_env > 0.03:
            canvas = K.motion_blur(canvas, amt * w_env, 0.0 if axis == "x" else 90.0)

    if kind != "split":
        canvas = K.apply_scrim_fast(canvas, SCRIM4_LOWER)

    if "callout" in sh and local_t > 0.10:
        cb = sh["callout"]
        tin_c = K.clamp01((local_t - 0.10) / 0.24) * K.clamp01((dur - local_t) / 0.15)
        K.paste_rgba(canvas, cb, 78, 134, tin_c)

    for (img, lx, ly, t0, style) in lines:
        M.draw_line(canvas, img, lx, ly, local_t, t0, dur, style)

    hud_overlay_4x5(canvas, t, sh["lens"])
    return K.finish_fast(canvas, VIG4, GRAINS4[idx % len(GRAINS4)])


def build_feed_4x5():
    print("=== GENERANDO ADAPTACIÓN NATIVA 4:5 FEED (1080x1350 · 30 FPS) ===")
    log_f = open("/tmp/ff_4x5.log", "wb")
    cmd = [
        M.FFMPEG, "-y",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{FW}x{FH}", "-r", str(FPS_FEED),
        "-i", "-",
        "-i", M.AUDIO,
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-profile:v", "high", "-pix_fmt", "yuv420p",
        "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        "-movflags", "+faststart", "-shortest",
        OUT_FEED_4X5,
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=log_f)
    for i in range(N_FEED):
        fr = render_frame_4x5(i)
        proc.stdin.write(fr.tobytes())
        if i == 428:  # t = 14.27 s
            Image.fromarray(fr).save(POSTER_4X5, quality=95)
        if (i + 1) % 150 == 0 or i == N_FEED - 1:
            print(f"  [4:5 Feed] {i + 1}/{N_FEED} frames", flush=True)
    proc.stdin.close()
    rc = proc.wait()
    log_f.close()
    if rc != 0:
        raise RuntimeError(open("/tmp/ff_4x5.log", "rb").read().decode(errors="ignore")[-1500:])
    print(f"Adaptación 4:5 Feed lista -> {OUT_FEED_4X5}")


if __name__ == "__main__":
    build_hook_b()
    build_feed_4x5()
