#!/usr/bin/env python3
"""
build_reel_17s.py — Reel Motion Design 3D de 17.00 s para Abyss Tattoo Studio
(José Joaquín Pérez 528, San Bernardo) según STORYBOARD_REEL_MOTION_3D_17S.md.

Escaleta implementada (1080x1920 · 60 fps · H.264/BT.709 · AAC 48 kHz):
  S1 00.00–01.60  Macro proceso real (proceso_detalle.mp4, HLG->BT.709)
                  Crash zoom + parallax + micro camera-shake      EL ARTE SE LLEVA EN LA PIEL
  S2 01.60–04.20  plate_p02 lobo/samurái + plate_p03 hombro realismo
                  Push-in 3D / pull-back alternados + whip-pan     PIEZAS ÚNICAS · DISEÑO AUTORAL
  S3 04.20–06.60  Fachada real 528 (plate_p01 <- fachada.jpg) + vitrina (plate_p08 <- vitrina.jpg)
                  Dolly-in con tilt-up 3D + HUD discreto           ABYSS TATTOO STUDIO / J. J. PÉREZ 528
  S4 06.60–10.00  proceso_filmacion.mp4 + proceso_pierna.mp4
                  Speed ramp + transición ink-wipe + perspectiva   TÉCNICA · DETALLE · PRECISIÓN
  S5 10.00–12.80  plate_p06 hélix titanio + plate_p07 septum titanio
                  Split-screen macro, movimientos opuestos         TATUAJES · PIERCING · JOYERÍA
  S6 12.80–17.00  Emblema oficial sobre mejor plano de portafolio
                  Pull-back + settle elástico + shimmer en CTA     RESERVA TU HORA / WHATSAPP / 528

Requiere audio de film/reel_abyss_17s_audio.wav (generar con build_reel_audio_17s.py).
Las placas de video intermedias se derivan en /tmp desde film/*.mp4 (no se versionan).

Uso:
  .venv/bin/python scripts/build_reel_audio_17s.py
  .venv/bin/python scripts/build_reel_17s.py --proofs   # lámina de pruebas (sin codificar)
  .venv/bin/python scripts/build_reel_17s.py            # máster 60fps + WhatsApp + láminas
"""

import argparse
import os
import shutil
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
os.chdir(ROOT)

import reel_kit as K  # noqa: E402


def resolve_ffmpeg() -> str:
    local_venv = os.path.join(ROOT, ".venv/bin/ffmpeg")
    if os.path.exists(local_venv):
        return local_venv
    sys_ff = shutil.which("ffmpeg")
    if sys_ff:
        return sys_ff
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


FFMPEG = resolve_ffmpeg()
FPS = 60
DUR = 17.0
N = int(round(DUR * FPS))  # 1020 frames exactos

AUDIO = "film/reel_abyss_17s_audio.wav"
OUT_SOCIAL = "film/reel_comercial_abyss_17s_1080x1920_60fps_social.mp4"
OUT_WHATSAPP = "film/reel_comercial_abyss_17s_720x1280_30fps_whatsapp.mp4"
COVER_HOOK = "film/reel_comercial_abyss_17s_cover_hook.jpg"
POSTER_CTA = "film/reel_comercial_abyss_17s_poster_cta.jpg"
STORYBOARD = "film/storyboard_reel_abyss_17s.jpg"

PLATES = "assets/reel_plates"
VPLATES = "/tmp/abyss_17s_plates"

REQUIRED = [
    "assets/reel_plates/emblema_abyss_alpha.png",
    "assets/reel_plates/plate_p01_fachada_real.jpg",
    "assets/reel_plates/plate_p02_lobo_samurai.jpg",
    "assets/reel_plates/plate_p03_hombro_realismo.jpg",
    "assets/reel_plates/plate_p06_helix_titanio.jpg",
    "assets/reel_plates/plate_p07_septum_titanio.jpg",
    "assets/reel_plates/plate_p08_vitrina_estudio.jpg",
    "assets/estudio/fachada.jpg",
    "assets/estudio/vitrina.jpg",
    "assets/estudio/maestro.jpg",
    "film/proceso_detalle.mp4",
    "film/proceso_filmacion.mp4",
    "film/proceso_pierna.mp4",
    AUDIO,
]


def preflight():
    print("=== PREFLIGHT 17s — existencia y reproducción de cada recurso ===")
    for path in REQUIRED:
        if not os.path.isfile(path):
            raise FileNotFoundError(f"Falta recurso requerido: {path} "
                                    "(si falta el WAV, ejecuta scripts/build_reel_audio_17s.py)")
        if path.endswith(".mp4"):
            cap = cv2.VideoCapture(path)
            n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            vfps = cap.get(cv2.CAP_PROP_FPS) or 30.0
            ok = n > 0 and cap.read()[0]
            cap.release()
            print(f"  [clip]  {path}: {n} frames @ {vfps:.1f} fps = {n / vfps:.2f}s, decode={'OK' if ok else 'FAIL'}")
            if not ok:
                raise RuntimeError(f"Clip no reproducible: {path}")
        elif path.endswith((".jpg", ".png")):
            im = Image.open(path)
            im.verify()
            print(f"  [still] {path}: {im.size[0]}x{im.size[1]} OK")
        else:
            print(f"  [audio] {path}: {os.path.getsize(path) / 1024:.0f} KB OK")


# ---------------------------------------------------------------- placas de video derivadas (film/*.mp4 -> overscan etalonado en /tmp)
VIDEO_PLATES = [
    # nombre, fuente, ss, dur, hdr_hlg, fx, fy, warm, contrast, sat
    ("v17_macro_detalle.mp4", "film/proceso_detalle.mp4", 4.05, 1.95, True, 0.52, 0.48, 0.06, 1.10, 0.90),
    ("v17_proceso_filmacion.mp4", "film/proceso_filmacion.mp4", 2.35, 2.35, False, 0.50, 0.46, 0.06, 1.09, 0.92),
    ("v17_proceso_pierna.mp4", "film/proceso_pierna.mp4", 1.15, 2.35, False, 0.50, 0.46, 0.06, 1.09, 0.90),
]


def ensure_video_plates(force=False):
    import prepare_commercial_assets as P  # reutiliza HLG->SDR + LightCraft + overscan del pipeline

    os.makedirs(VPLATES, exist_ok=True)
    for name, src, ss, dur, hdr, fx, fy, warm, contrast, sat in VIDEO_PLATES:
        out_path = os.path.join(VPLATES, name)
        if os.path.exists(out_path) and not force:
            print(f"  [cache] {name}")
            continue
        cap = cv2.VideoCapture(src)
        vfps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(round(ss * vfps)))
        n = int(round(dur * vfps))
        proc = subprocess.Popen(
            [FFMPEG, "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", "1296x2304", "-r", f"{vfps:.3f}",
             "-i", "-", "-an", "-c:v", "libx264", "-preset", "fast", "-crf", "15", "-pix_fmt", "yuv420p",
             "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", out_path],
            stdin=subprocess.PIPE, stderr=subprocess.DEVNULL,
        )
        written, last = 0, None
        for _ in range(n):
            ok, frame = cap.read()
            if not ok:
                if last is None:
                    break
                frame = last.copy()
            else:
                last = frame
            if hdr:
                frame = P.hlg_to_sdr_bgr(frame)
            frame = P.lightcraft_grade_bgr(P.crop_to_aspect_overscan(frame, fx=fx, fy=fy),
                                           warmth=warm, contrast=contrast, sat=sat)
            proc.stdin.write(frame.tobytes())
            written += 1
        cap.release()
        proc.stdin.close()
        if proc.wait() != 0 or written == 0:
            raise RuntimeError(f"Fallo al derivar placa {name}")
        print(f"  [video] {name} ({written} frames @ {vfps:.1f}fps) <- {src} ss={ss}s")


# ---------------------------------------------------------------- carga / muestreo de placas
still_cache = {}
video_cache = {}


def load_still_rgb(name: str) -> np.ndarray:
    if name not in still_cache:
        if len(still_cache) >= 4:
            still_cache.clear()
        bgr = cv2.imread(os.path.join(PLATES, name))
        if bgr is None:
            raise FileNotFoundError(name)
        still_cache[name] = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    return still_cache[name]


def load_video_rgb(name: str):
    if name not in video_cache:
        video_cache.clear()  # solo la toma activa en RAM
        cap = cv2.VideoCapture(os.path.join(VPLATES, name))
        vfps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        frames = []
        while True:
            ok, f = cap.read()
            if not ok:
                break
            frames.append(cv2.cvtColor(f, cv2.COLOR_BGR2RGB))
        cap.release()
        if not frames:
            raise RuntimeError(f"Placa de video vacía: {name}")
        video_cache[name] = (frames, vfps)
    return video_cache[name]


def sample_still(name: str) -> np.ndarray:
    return load_still_rgb(name)


def sample_video(name: str, src_t: float) -> np.ndarray:
    """Muestra la placa de video en el instante fuente absoluto src_t (con blend sub-frame)."""
    frames, vfps = load_video_rgb(name)
    idx = src_t * vfps
    n = len(frames)
    i0 = min(n - 1, max(0, int(idx)))
    i1 = min(n - 1, i0 + 1)
    fr = idx - int(idx)
    if fr < 0.02 or i0 == i1:
        return frames[i0]
    return cv2.addWeighted(frames[i0], 1.0 - fr, frames[i1], fr, 0)


# ---------------------------------------------------------------- elementos gráficos reutilizables
HUD = K.corner_hud(132)
HUD_SOFT = K.corner_hud(68)
REC_TAG = K.tracked_text("REC", K.font("mont700", 19), K.CREAM, 6, shadow=True)
BRAND_TOP = K.tracked_text("ABYSS  ·  SAN BERNARDO", K.font("mont600", 19), K.BONE, 7, shadow=True)
SCRIM_LOWER = K.make_scrim_lut("lower")
SCRIM_HERO = K.make_scrim_lut("hero_center")
VIGNETTE_U16 = K.make_vignette_u16(0.36, 2.25)
GRAINS_I16 = K.make_grain_tiles_i16(8, 1.8)

_yy, _xx = np.mgrid[0:K.H, 0:K.W].astype(np.float32)
DIAG = (_xx + _yy * 0.35) / (K.W + K.H * 0.35)  # coordenada diagonal normalizada (wipe + especular)
del _yy, _xx

LENS_TAGS = {}


def lens_tag(txt: str) -> np.ndarray:
    if txt not in LENS_TAGS:
        LENS_TAGS[txt] = K.tracked_text(txt, K.font("mont600", 18), K.BONE, 5, shadow=True)
    return LENS_TAGS[txt]


def draw_progress_bar(canvas: np.ndarray, t: float):
    y = 182
    x0, x1 = 64, 1016
    canvas[y : y + 2, x0:x1] = (canvas[y : y + 2, x0:x1].astype(np.uint16) * 180 >> 8).astype(np.uint8) + 22
    xp = int(round(x0 + (x1 - x0) * K.clamp01(t / DUR)))
    canvas[y : y + 3, x0:xp] = np.array(K.TEAL_L, dtype=np.uint8)


def hud_overlay(canvas: np.ndarray, t: float, lens: str, soft: bool = False):
    K.paste_rgba(canvas, HUD_SOFT if soft else HUD, 0, 0, 1.0)
    K.paste_rgba(canvas, BRAND_TOP, 540 - BRAND_TOP.shape[1] // 2, 134, 0.72 if soft else 0.90)
    if not soft:
        draw_progress_bar(canvas, t)
        blink = 0.35 + 0.65 * (0.5 + 0.5 * np.sin(t * 2 * np.pi * 1.25))
        im_dot = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
        ImageDraw.Draw(im_dot).ellipse((2, 2, 14, 14), fill=(214, 72, 62, int(255 * blink)))
        K.paste_rgba(canvas, np.array(im_dot), 90, 224, 1.0)
        K.paste_rgba(canvas, REC_TAG, 112, 214, 0.90)
        lt = lens_tag(lens)
        K.paste_rgba(canvas, lt, 1002 - lt.shape[1], 215, 0.88)


def draw_line(canvas, img, cx, cy, local_t, t0, dur_shot, style="rise"):
    if local_t < t0:
        return
    tin = K.clamp01((local_t - t0) / 0.24)
    tout = K.clamp01((dur_shot - local_t) / 0.14) if style != "hold" else 1.0
    a = K.ease_out_cubic(tin) * tout
    if style == "rise":
        dy = (1.0 - K.ease_out_quart(tin)) * 30.0
        sc = 1.0
    elif style == "pop":
        dy = 0.0
        sc = 0.86 + 0.14 * K.ease_out_back(tin, 1.55)
    elif style == "punch":
        dy = 0.0
        sc = 1.13 - 0.13 * K.ease_out_quint(tin)
    else:
        dy, sc = 0.0, 1.0
    if abs(sc - 1.0) > 1e-3:
        nw = max(2, int(round(img.shape[1] * sc)))
        nh = max(2, int(round(img.shape[0] * sc)))
        im = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_LINEAR)
    else:
        im = img
    K.paste_rgba(canvas, im, cx - im.shape[1] / 2.0, cy - im.shape[0] / 2.0 + dy, a)


def whip_envelope(local_t: float, dur: float, window: float = 0.16) -> float:
    a = max(0.0, 1.0 - local_t / window)
    b = max(0.0, 1.0 - (dur - local_t) / window)
    return max(a, b) ** 2.0


# ---------------------------------------------------------------- ESCALETA 17 s (fiel al storyboard)
SHOTS = [
    # S1 — Macro proceso real: crash zoom desde macro, entrada inmediata en el primer frame
    dict(
        t0=0.00, t1=1.60, kind="single_video",
        plate="v17_macro_detalle.mp4", speed=1.0, offset=0.05,
        cam=K.Camera(z=(1.14, 1.36), c=((0.57, 0.40), (0.56, 0.50)), ease="out", rot=(1.4, 0.0), shake=0.30, seed=1),
        lens="ECU MACRO · 100mm",
        scrim="hero",
        zoom_blur_head=0.50,
        flash_head=(0.22, K.PAPER),
        lines=K.stack([
            ("EL ARTE SE LLEVA", "cinzel800", 70, K.PAPER, 4, 0.10, "punch", "display"),
            ("EN LA PIEL", "cinzel800", 70, K.PAPER, 4, 0.30, "punch", "display"),
        ], top=1190, block_gap=0.34),
    ),
    # S2 — Piezas reales: push-in 3D (lobo) / pull-back (hombro), whip-pan al beat (2.90)
    dict(
        t0=1.60, t1=4.20, kind="dual_cut", split_at=1.30,
        plate_a="plate_p02_lobo_samurai.jpg",
        cam_a=K.Camera(z=(1.05, 1.24), c=((0.50, 0.45), (0.46, 0.42)), ease="out", rot=(-1.6, 0.0)),
        plate_b="plate_p03_hombro_realismo.jpg",
        cam_b=K.Camera(z=(1.24, 1.06), c=((0.54, 0.40), (0.52, 0.44)), ease="out", rot=(1.4, 0.0)),
        lens="DETALLE REALISMO · 50mm",
        scrim="lower",
        whip=("x", 24),
        flash_head=(0.12, K.PAPER),
        lines=K.stack([
            ("PIEZAS ÚNICAS", "cinzel800", 76, K.PAPER, 5, 0.08, "punch", "display"),
            ("DISEÑO AUTORAL", "mont600", 25, K.TEAL_L, 9, 0.30, "rise", "label"),
        ], top=1215, block_gap=0.46),
    ),
    # S3 — Estudio: fachada real 528 dolly-in + tilt-up 3D, luego vitrina
    dict(
        t0=4.20, t1=6.60, kind="dual_cut", split_at=1.20,
        plate_a="plate_p01_fachada_real.jpg",
        cam_a=K.Camera(z=(1.04, 1.20), c=((0.52, 0.52), (0.56, 0.40)), ease="out", tilt=((1.4, 1.6), (0.0, 0.0))),
        plate_b="plate_p08_vitrina_estudio.jpg",
        cam_b=K.Camera(z=(1.05, 1.19), c=((0.50, 0.56), (0.50, 0.47)), ease="inout", tilt=((0.0, 1.2), (0.0, 0.0))),
        lens="PLANO GENERAL · 24mm",
        scrim="lower",
        zoom_blur_head=0.30,
        callout=K.callout_badge("DIRECCIÓN OFICIAL", "J. J. PÉREZ 528"),
        lines=K.stack([
            ("ABYSS TATTOO STUDIO", "cinzel800", 56, K.PAPER, 4, 0.08, "punch", "display"),
            ("JOSÉ JOAQUÍN PÉREZ 528", "mont700", 27, K.CREAM, 6, 0.26, "rise", "label"),
        ], top=1225, block_gap=0.46),
    ),
    # S4 — Proceso: speed ramp en ambos clips + ink-wipe en el corte interno (8.30)
    dict(
        t0=6.60, t1=10.00, kind="dual_video", split_at=1.70,
        plate_a="v17_proceso_filmacion.mp4", span_a=2.05, offset_a=0.05,
        cam_a=K.Camera(z=(1.06, 1.22), c=((0.50, 0.47), (0.48, 0.44)), ease="out", shake=0.16, seed=4),
        plate_b="v17_proceso_pierna.mp4", span_b=2.05, offset_b=0.05,
        cam_b=K.Camera(z=(1.05, 1.24), c=((0.47, 0.46), (0.41, 0.41)), ease="inout", tilt=((0.0, 0.0), (0.8, -0.6))),
        lens="PPP DETALLE · 85mm",
        scrim="lower",
        whip=("x", 16),
        lines=K.stack([
            ("TÉCNICA", "cinzel800", 62, K.PAPER, 5, 0.10, "punch", "display"),
            ("DETALLE", "cinzel800", 62, K.PAPER, 5, 0.44, "punch", "display"),
            ("PRECISIÓN", "cinzel800", 62, K.PAPER, 5, 0.78, "punch", "display"),
        ], top=1125, block_gap=0.34),
    ),
    # S5 — Split-screen macro piercing/joyería con movimientos opuestos + reflejo especular
    dict(
        t0=10.00, t1=12.80, kind="split",
        top_plate="plate_p06_helix_titanio.jpg",
        bot_plate="plate_p07_septum_titanio.jpg",
        # Centros medidos sobre grilla: gemas hélix (0.47,0.27)+cadena; arco septum y~0.50-0.67
        top_cam=K.Camera(z=(1.16, 1.04), c=((0.50, 0.37), (0.53, 0.42)), ease="out"),
        bot_cam=K.Camera(z=(1.06, 1.14), c=((0.49, 0.56), (0.46, 0.58)), ease="out"),
        lens="DOBLE MACRO · 100mm",
        whip=("x", 20),
        lines=K.stack([
            ("TATUAJES · PIERCING · JOYERÍA", "mont800", 27, K.PAPER, 3, 0.10, "punch", "display", False),
        ], top=936, block_gap=0.40),
    ),
    # S6 — Packshot CTA
    dict(
        t0=12.80, t1=17.00, kind="cta",
        lens="ABYSS · J. J. PÉREZ 528",
    ),
]

# Validación de zona segura: ningún título supera 900 px de ancho (centrado: x en [90, 990])
for _sh in SHOTS:
    for _img, *_rest in _sh.get("lines", []):
        if _img.shape[1] > 900:
            raise SystemExit(f"Línea tipográfica fuera de zona segura: {_img.shape[1]}px en plano {_sh['t0']}s")

TAG_HELIX = K.tracked_text("HÉLIX", K.font("mont700", 20), K.CREAM, 6, shadow=True)
TAG_SEPTUM = K.tracked_text("SEPTUM", K.font("mont700", 20), K.CREAM, 6, shadow=True)

# ---------------------------------------------------------------- elementos del CTA (12.80–17.00)
EMBLEM = K.load_rgba(os.path.join(PLATES, "emblema_abyss_alpha.png"), (320, 320))
CTA_GLOW = K.glow(480, K.TEAL, 82.0)
CTA_RINGS = K.concentric_rings(790, rings=8, color=K.BONE, max_alpha=30)
CTA_DIV = K.divider(520, K.BONE, K.TEAL_L, 215, r=8)
# Botón visual de WhatsApp: sin número ni enlace largo incrustados (el link va en la publicación)
CTA_PILL = K.pill(
    "ESCRÍBENOS POR WHATSAPP",
    "mont800", 29, 3,
    fg=K.OBSIDIAN, bg=K.PAPER, border=K.BONE_L,
    pad_x=42, pad_y=23, with_diamond=True, diamond_color=K.SAGE,
)
CTA_TITLE = K.tracked_text("RESERVA TU HORA", K.font("cinzel800", 72), K.PAPER, 5, shadow=True)
CTA_HANDLE = K.tracked_text("@abyss_tattoo_studio", K.font("mont700", 27), K.CREAM, 4, shadow=True)
CTA_ADDR = K.pill(
    "SAN BERNARDO · J. J. PÉREZ 528",
    "mont700", 20, 4,
    fg=K.TEAL_L, bg=(24, 20, 17), border=K.SAGE,
    pad_x=28, pad_y=12, with_diamond=False,
)
for _el, _nm in [(CTA_TITLE, "CTA_TITLE"), (CTA_PILL, "CTA_PILL"), (CTA_ADDR, "CTA_ADDR"), (CTA_HANDLE, "CTA_HANDLE")]:
    if _el.shape[1] > 900:
        raise SystemExit(f"Elemento CTA fuera de zona segura: {_nm} = {_el.shape[1]}px")


def cta_bg_base() -> np.ndarray:
    """Mejor plano de portafolio (lobo/samurái) desenfocado en Obsidiana como fondo del packshot."""
    bg = cv2.GaussianBlur(load_still_rgb("plate_p02_lobo_samurai.jpg"), (0, 0), 34)
    return np.clip(bg.astype(np.float32) * 0.24 + np.array(K.OBSIDIAN, np.float32) * 0.78, 0, 255).astype(np.uint8)


CTA_BG_BASE = cta_bg_base()


def render_cta(local_t: float, dur: float) -> np.ndarray:
    p = local_t / dur
    # Pull-back final a composición limpia (zoom-out continuo y suave)
    z, cx, cy, *_ = K.Camera(z=(1.16, 1.03), c=((0.50, 0.44), (0.50, 0.48)), ease="out").state(p)
    canvas = K.render_camera(CTA_BG_BASE, z, cx, cy)

    g_alpha = 0.72 + 0.18 * np.sin(local_t * 2.2)
    K.paste_rgba(canvas, CTA_GLOW, center=True, y=445 - CTA_GLOW.shape[0] // 2, alpha=g_alpha * K.clamp01(local_t / 0.35))
    K.paste_rgba(canvas, CTA_RINGS, center=True, y=445 - CTA_RINGS.shape[0] // 2, alpha=0.85 * K.clamp01(local_t / 0.5))

    # Emblema oficial con settle elástico + flotación mínima para sostener los 4.2 s
    tin = K.clamp01(local_t / 0.45)
    sc = 0.84 + 0.16 * K.ease_out_back(tin, 1.35)
    float_y = int(round(4.0 * np.sin(local_t * 1.4))) if local_t > 0.6 else 0
    ew = max(2, int(round(EMBLEM.shape[1] * sc)))
    eh = max(2, int(round(EMBLEM.shape[0] * sc)))
    emb = cv2.resize(EMBLEM, (ew, eh), interpolation=cv2.INTER_LINEAR)
    K.paste_rgba(canvas, emb, 540 - ew // 2, 445 - eh // 2 + float_y, K.ease_out_cubic(tin))

    draw_line(canvas, CTA_TITLE, 540, 700, local_t, 0.20, dur, "punch")
    K.paste_rgba(canvas, CTA_DIV, 540 - CTA_DIV.shape[1] // 2, 782 - CTA_DIV.shape[0] // 2,
                 K.clamp01((local_t - 0.45) / 0.26))

    # Botón WhatsApp con pop elástico + dos barridos especulares (0.95 s y 2.60 s locales)
    if local_t >= 0.60:
        bt = K.clamp01((local_t - 0.60) / 0.30)
        bsc = 0.88 + 0.12 * K.ease_out_back(bt, 1.55)
        bw = max(2, int(round(CTA_PILL.shape[1] * bsc)))
        bh = max(2, int(round(CTA_PILL.shape[0] * bsc)))
        pill_im = cv2.resize(CTA_PILL, (bw, bh), interpolation=cv2.INTER_LINEAR)
        shimmer_p = -1.0
        if 0.95 <= local_t <= 1.80:
            shimmer_p = (local_t - 0.95) / 0.85
        elif 2.60 <= local_t <= 3.45:
            shimmer_p = (local_t - 2.60) / 0.85
        K.paste_rgba_shimmer(canvas, pill_im, 540, 888, K.ease_out_cubic(bt), shimmer_p)

    draw_line(canvas, CTA_HANDLE, 540, 1002, local_t, 0.85, dur, "hold")
    draw_line(canvas, CTA_ADDR, 540, 1085, local_t, 1.00, dur, "hold")

    if local_t < 0.16:
        canvas = K.flash_frame(canvas, 0.30 * (1.0 - local_t / 0.16) ** 2.0, K.PAPER)

    hud_overlay(canvas, 12.80 + local_t, "ABYSS · J. J. PÉREZ 528", soft=True)

    # Respiro de loop: caída suave a Obsidiana en los últimos 0.22 s
    if dur - local_t < 0.22:
        fade = 0.42 * (1.0 - (dur - local_t) / 0.22) ** 2.0
        canvas = K.flash_frame(canvas, fade, K.OBSIDIAN)
    return canvas


def render_split(sh: dict, local_t: float, dur: float) -> np.ndarray:
    p = local_t / dur
    canvas = np.zeros((K.H, K.W, 3), dtype=np.uint8)
    band_top, band_bot = 878, 1042
    vh_top = band_top
    vh_bot = K.H - band_bot

    zt, cxt, cyt, rott, txt, tyt = sh["top_cam"].state(p)
    canvas[:band_top] = K.render_camera(sample_still(sh["top_plate"]), zt, cxt, cyt, rott, txt, tyt,
                                        out_w=K.W, out_h=vh_top)
    zb, cxb, cyb, rotb, txb, tyb = sh["bot_cam"].state(p)
    canvas[band_bot:] = K.render_camera(sample_still(sh["bot_plate"]), zb, cxb, cyb, rotb, txb, tyb,
                                        out_w=K.W, out_h=vh_bot)
    canvas[band_top:band_bot] = np.array(K.OBSIDIAN, dtype=np.uint8)

    # Reflejo especular controlado: barrido diagonal de luz sobre ambas mitades (joyería)
    sweep_p = (local_t - 0.55) / 1.15
    if 0.0 <= sweep_p <= 1.0:
        pos = -0.1 + 1.2 * sweep_p
        band = np.exp(-((DIAG - pos) ** 2) / 0.0016) * 20.0
        band[band_top:band_bot] = 0.0
        canvas = np.clip(canvas.astype(np.float32) + band[..., None], 0, 255).astype(np.uint8)

    im = Image.fromarray(canvas)
    d = ImageDraw.Draw(im)
    d.line([(0, band_top), (K.W, band_top)], fill=K.BONE, width=3)
    d.line([(0, band_bot), (K.W, band_bot)], fill=K.BONE, width=3)
    d.line([(64, band_top + 10), (1016, band_top + 10)], fill=K.SAGE, width=1)
    d.line([(64, band_bot - 10), (1016, band_bot - 10)], fill=K.SAGE, width=1)
    K.diamond(d, 92, (band_top + band_bot) // 2, 8, K.TEAL_L, 255)
    K.diamond(d, K.W - 92, (band_top + band_bot) // 2, 8, K.TEAL_L, 255)
    canvas = np.array(im)

    if local_t > 0.22:
        a = K.clamp01((local_t - 0.22) / 0.25) * K.clamp01((dur - local_t) / 0.15)
        K.paste_rgba(canvas, TAG_HELIX, 88, band_top - 64, a * 0.92)
        K.paste_rgba(canvas, TAG_SEPTUM, 88, band_bot + 28, a * 0.92)
    return canvas


def ink_wipe(a: np.ndarray, b: np.ndarray, u: float) -> np.ndarray:
    """Barrido de tinta diagonal con borde oscuro Obsidiana y filete Salvia (u en [0,1])."""
    th = -0.15 + 1.30 * u
    mask = np.clip((th - DIAG) / 0.10 + 0.5, 0.0, 1.0)[..., None]  # 1 -> plano B
    edge = np.exp(-((DIAG - th) ** 2) / 0.00035)[..., None]
    out = a.astype(np.float32) * (1.0 - mask) + b.astype(np.float32) * mask
    out = out * (1.0 - 0.72 * edge) + np.array(K.SAGE, np.float32)[None, None, :] * (0.30 * edge)
    return np.clip(out, 0, 255).astype(np.uint8)


def shot_at(t: float) -> dict:
    for s in SHOTS:
        if s["t0"] <= t < s["t1"]:
            return s
    return SHOTS[-1]


def render_frame(idx: int) -> np.ndarray:
    t = idx / FPS
    sh = shot_at(t)
    local_t = t - sh["t0"]
    dur = sh["t1"] - sh["t0"]
    p = local_t / dur
    kind = sh["kind"]

    if kind == "cta":
        return K.finish_fast(render_cta(local_t, dur), VIGNETTE_U16, GRAINS_I16[idx % len(GRAINS_I16)])

    if kind == "split":
        canvas = render_split(sh, local_t, dur)
    elif kind == "dual_cut":
        split_at = sh["split_at"]
        if local_t < split_at:
            sub_p = local_t / split_at
            src, cam = sample_still(sh["plate_a"]), sh["cam_a"]
        else:
            sub_p = (local_t - split_at) / (dur - split_at)
            src, cam = sample_still(sh["plate_b"]), sh["cam_b"]
        z, cx, cy, rot, tx, ty = cam.state(sub_p)
        canvas = K.render_camera(src, z, cx, cy, rot, tx, ty)
        d_split = abs(local_t - split_at)
        if d_split < 0.10:  # whip-pan + flash en el corte interno sincronizado al beat
            env = (1.0 - d_split / 0.10) ** 2.0
            canvas = K.motion_blur(canvas, 24 * env, 0.0)
            canvas = K.flash_frame(canvas, 0.20 * env, K.CREAM)
    elif kind == "dual_video":
        split_at = sh["split_at"]

        def render_side(is_b: bool, lt: float, sub_dur: float):
            sub_p = K.clamp01(lt / sub_dur)
            if is_b:
                src = sample_video(sh["plate_b"], sh["offset_b"] + K.ease_speed_ramp(sub_p) * sh["span_b"])
                cam = sh["cam_b"]
            else:
                src = sample_video(sh["plate_a"], sh["offset_a"] + K.ease_speed_ramp(sub_p) * sh["span_a"])
                cam = sh["cam_a"]
            z, cx, cy, rot, tx, ty = cam.state(sub_p)
            return K.render_camera(src, z, cx, cy, rot, tx, ty)

        wipe_half = 0.16
        if abs(local_t - split_at) < wipe_half:
            a_im = render_side(False, min(local_t, split_at), split_at)
            b_im = render_side(True, max(0.0, local_t - split_at), dur - split_at)
            canvas = ink_wipe(a_im, b_im, (local_t - (split_at - wipe_half)) / (2 * wipe_half))
        elif local_t < split_at:
            canvas = render_side(False, local_t, split_at)
        else:
            canvas = render_side(True, local_t - split_at, dur - split_at)
    else:  # single_video
        src = sample_video(sh["plate"], sh.get("offset", 0.0) + local_t * sh.get("speed", 1.0))
        z, cx, cy, rot, tx, ty = sh["cam"].state(p)
        canvas = K.render_camera(src, z, cx, cy, rot, tx, ty)

    if "whip" in sh:
        axis, amt = sh["whip"]
        w_env = whip_envelope(local_t, dur)
        if w_env > 0.03:
            canvas = K.motion_blur(canvas, amt * w_env, 0.0 if axis == "x" else 90.0)
    if "zoom_blur_head" in sh and local_t < 0.26:
        canvas = K.radial_zoom_blur(canvas, sh["zoom_blur_head"] * (1.0 - local_t / 0.26) ** 1.8)

    if kind != "split":
        canvas = K.apply_scrim_fast(canvas, SCRIM_HERO if sh.get("scrim") == "hero" else SCRIM_LOWER)

    if "callout" in sh and local_t > 0.10:
        tin_c = K.clamp01((local_t - 0.10) / 0.24) * K.clamp01((dur - local_t) / 0.15)
        K.paste_rgba(canvas, sh["callout"], 86, 276, tin_c)

    for (img, lx, ly, t0, style) in sh.get("lines", []):
        draw_line(canvas, img, lx, ly, local_t, t0, dur, style)

    if "flash_head" in sh and local_t < 0.12:
        amt, tint = sh["flash_head"]
        canvas = K.flash_frame(canvas, amt * (1.0 - local_t / 0.12) ** 2.0, tint)

    hud_overlay(canvas, t, sh["lens"])
    return K.finish_fast(canvas, VIGNETTE_U16, GRAINS_I16[idx % len(GRAINS_I16)])


# ---------------------------------------------------------------- láminas (pruebas + storyboard)
PROOF_POINTS = [
    (0.85, "S1 · 00:00.8 MACRO · EL ARTE EN LA PIEL"),
    (2.20, "S2a · 00:02.2 LOBO · PIEZAS ÚNICAS"),
    (3.60, "S2b · 00:03.6 HOMBRO · AUTORAL"),
    (4.90, "S3a · 00:04.9 FACHADA 528"),
    (6.00, "S3b · 00:06.0 VITRINA · 528"),
    (7.45, "S4a · 00:07.4 PROCESO · TÉCNICA"),
    (9.20, "S4b · 00:09.2 PROCESO · PRECISIÓN"),
    (11.40, "S5 · 00:11.4 SPLIT · PIERCING"),
    (15.90, "S6 · 00:15.9 CTA · RESERVA TU HORA"),
]


def compose_sheet(frames: dict, out_path: str, title: str):
    tw, th, lab_h, head_h = 356, 633, 46, 92
    cols, rows = 3, 3
    sheet = Image.new("RGB", (cols * tw, head_h + rows * (th + lab_h)), K.OBSIDIAN)
    d = ImageDraw.Draw(sheet)
    try:
        f_t = ImageFont.truetype("assets/fonts/cinzel-800.ttf", 30)
        f_s = ImageFont.truetype("assets/fonts/montserrat-600.ttf", 17)
        f_l = ImageFont.truetype("assets/fonts/montserrat-700.ttf", 15)
    except Exception:
        f_t = f_s = f_l = ImageFont.load_default()
    d.text((28, 16), title, font=f_t, fill=K.PAPER)
    d.text((28, 56), "1080x1920 · 60 fps · H.264 BT.709 · José Joaquín Pérez 528, San Bernardo", font=f_s, fill=K.BONE)
    for i, (t, label) in enumerate(PROOF_POINTS):
        if t not in frames:
            continue
        x = (i % cols) * tw
        y = head_h + (i // cols) * (th + lab_h)
        sheet.paste(Image.fromarray(frames[t]).resize((tw, th), Image.Resampling.LANCZOS), (x, y))
        d.rectangle((x, y + th, x + tw, y + th + lab_h), fill=(26, 21, 18))
        d.text((x + 10, y + th + 8), label, font=f_l, fill=K.CREAM)
        d.text((x + 10, y + th + 27), f"t = {t:.2f} s", font=f_s, fill=K.TEAL_L)
    sheet.save(out_path, quality=92)
    print(f"Lámina -> {out_path} ({sheet.size[0]}x{sheet.size[1]})")


def proofs():
    ensure_video_plates()
    frames = {}
    for t, label in PROOF_POINTS:
        idx = int(round(t * FPS))
        frames[t] = render_frame(idx)
        print(f"  prueba t={t:.2f}s (frame {idx}) — {label}")
    compose_sheet(frames, "/tmp/abyss17_proofs.jpg", "PRUEBAS — REEL MOTION 3D 17s · ABYSS")
    Image.fromarray(frames[0.85]).save("/tmp/abyss17_proof_s1.jpg", quality=94)
    Image.fromarray(frames[11.40]).save("/tmp/abyss17_proof_s5.jpg", quality=94)
    Image.fromarray(frames[15.90]).save("/tmp/abyss17_proof_cta.jpg", quality=94)
    print("Pruebas individuales: /tmp/abyss17_proof_s1.jpg · _s5.jpg · _cta.jpg")


# ---------------------------------------------------------------- codificación
def encode():
    preflight()
    ensure_video_plates()
    os.makedirs("film", exist_ok=True)
    cmd = [
        FFMPEG, "-y",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{K.W}x{K.H}", "-r", str(FPS),
        "-i", "-",
        "-i", AUDIO,
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-maxrate", "16M", "-bufsize", "32M",
        "-profile:v", "high", "-level", "4.2",
        "-pix_fmt", "yuv420p",
        "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        "-metadata", "title=Abyss Tattoo Studio — Reel Motion Design 3D 17s (J. J. Pérez 528, San Bernardo)",
        "-movflags", "+faststart", "-shortest", "-frames:v", str(N),
        OUT_SOCIAL,
    ]
    log_f = open("/tmp/ff_social_17s.log", "wb")
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=log_f)
    capture_at = {int(round(t * FPS)): t for t, _ in PROOF_POINTS}
    captured = {}
    for i in range(N):
        f = render_frame(i)
        proc.stdin.write(f.tobytes())
        if i in capture_at:
            captured[capture_at[i]] = f
        if (i + 1) % 120 == 0 or i == N - 1:
            print(f"  renderizado {i + 1}/{N} frames ({(i + 1) / FPS:.2f}s)", flush=True)
    proc.stdin.close()
    rc = proc.wait()
    log_f.close()
    if rc != 0:
        raise RuntimeError(open("/tmp/ff_social_17s.log", "rb").read().decode(errors="ignore")[-3000:])
    print(f"Máster social 60fps -> {OUT_SOCIAL}")

    Image.fromarray(captured[0.85]).save(COVER_HOOK, quality=94)
    Image.fromarray(captured[15.90]).save(POSTER_CTA, quality=95)
    compose_sheet(captured, STORYBOARD, "STORYBOARD — REEL MOTION 3D 17s · ABYSS TATTOO STUDIO")
    print(f"Portadas -> {COVER_HOOK} · {POSTER_CTA}")

    # Copia ligera para WhatsApp: 720x1280 @ 30 fps, techo 4.5 Mbps
    subprocess.run(
        [FFMPEG, "-y", "-i", OUT_SOCIAL,
         "-vf", "fps=30,scale=720:1280:flags=lanczos",
         "-c:v", "libx264", "-preset", "medium", "-crf", "23",
         "-maxrate", "4500k", "-bufsize", "9000k",
         "-profile:v", "high", "-pix_fmt", "yuv420p",
         "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
         "-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-movflags", "+faststart",
         OUT_WHATSAPP],
        check=True, stderr=subprocess.DEVNULL,
    )
    print(f"Copia WhatsApp 30fps -> {OUT_WHATSAPP}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--proofs", action="store_true", help="solo lámina de pruebas, sin codificar")
    ap.add_argument("--force-plates", action="store_true", help="re-derivar placas de video en /tmp")
    args = ap.parse_args()
    if args.force_plates:
        ensure_video_plates(force=True)
    if args.proofs:
        preflight()
        proofs()
    else:
        encode()
