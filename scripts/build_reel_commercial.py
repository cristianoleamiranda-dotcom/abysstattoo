#!/usr/bin/env python3
"""
build_reel_commercial.py — Montaje, rig virtual 3D y masterización del Reel Comercial de 15.00 s
para Abyss Tattoo Studio (José Joaquín Pérez 528, San Bernardo · Santiago).

Arquitectura rítmica a 100 BPM exactos (1 negra = 0.60 s = 36 frames @ 60 fps · total = 900 frames = 15.00 s):
  01  0.00– 1.20  ECU Macro · 100mm         video macro aguja      Crash pull-back + radial blur   ESTO NO ES / UN TATUAJE.
  02  1.20– 2.40  Primer Plano · 50mm       video chiaroscuro      Punch zoom-in + whip X          ES UNA FIRMA.
  03  2.40– 3.60  Gran Plano Aéreo · 16mm   video dron FPV 528     Hyper-dive + tilt 3D            JOSÉ JOAQUÍN PÉREZ 528
  04  3.60– 4.50  Plano General · 24mm      foto real fachada 528  Dolly-in + tilt-up 3D           DESDE 2009 · J. J. PÉREZ 528
  05  4.50– 5.40  Travelling POV · 24mm     video gimbal interior  Avance subjetivo + whip Y       CRUZA LA PUERTA
  06  5.40– 6.60  Plano Cenital · 35mm      video cabina estéril   Órbita picada + push-in         ZONA SEREMI
  07  6.60– 7.80  PPP Detalle · 85mm        video Ink Wipe HDR     Over-the-shoulder push-in       TRAZO A TRAZO
  08  7.80– 9.00  Montaje Realismo · 50mm   lobo + hombro (corte)  Crash zoom-in / pull-back       PIEZA ÚNICA
  09  9.00–10.20  Montaje Autoral · 35/50   manga + full color     Tilt vertical + whip lateral    DISEÑO AUTORAL
  10 10.20–11.40  Doble Macro · 100mm       hélix + septum F136    Split-screen zooms opuestos     TITANIO ASTM F136
  11 11.40–12.60  Plano Medio · 50mm        video artista cabina   Dolly push-in + riser sonoro    5 ARTISTAS
  12 12.60–15.00  Packshot CTA · Cierre     emblema + botón CTA    Settle elástico + shimmer       AGENDA TU HORA · +56 9 4778 6839 · 528
"""

import os
import shutil
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw

ROOT = "/home/user/abysstattoo"
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
DUR = 15.0
N = int(round(DUR * FPS))  # 900 frames exactos

AUDIO = "film/reel_abyss_15s_audio.wav"
OUT_SOCIAL = "film/reel_comercial_abyss_15s_1080x1920_60fps_social.mp4"
OUT_WEB = "film/reel_comercial_abyss_15s_1080x1920_30fps_web.mp4"
POSTER_CTA = "film/reel_comercial_abyss_15s_poster_cta.jpg"
COVER_HOOK = "film/reel_comercial_abyss_15s_cover_hook.jpg"

PLATES = "assets/reel_plates"

# ---------------------------------------------------------------- carga de placas en RAM
still_cache = {}
video_cache = {}


def load_still_rgb(name: str) -> np.ndarray:
    if name not in still_cache:
        if len(still_cache) >= 3:
            still_cache.clear()
        bgr = cv2.imread(os.path.join(PLATES, name))
        if bgr is None:
            raise FileNotFoundError(name)
        still_cache[name] = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    return still_cache[name]


def load_video_rgb(name: str):
    if name not in video_cache:
        video_cache.clear()  # mantiene solo la toma activa en RAM (< 650 MB pico total)
        cap = cv2.VideoCapture(os.path.join(PLATES, name))
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


def sample_plate(name: str, local_t: float, speed: float = 1.0, offset: float = 0.0) -> np.ndarray:
    if name.endswith(".jpg") or name.endswith(".png"):
        return load_still_rgb(name)
    frames, vfps = load_video_rgb(name)
    idx = (offset + local_t * speed) * vfps
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

LENS_TAGS = {}


def lens_tag(txt: str) -> np.ndarray:
    if txt not in LENS_TAGS:
        LENS_TAGS[txt] = K.tracked_text(txt, K.font("mont600", 18), K.BONE, 5, shadow=True)
    return LENS_TAGS[txt]


def draw_progress_bar(canvas: np.ndarray, t: float):
    """Barra de progreso minimalista de 2 px dentro de la zona segura superior."""
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
        dot = np.zeros((16, 16, 4), np.uint8)
        d = ImageDraw.Draw(Image.fromarray(dot))
        im_dot = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
        ImageDraw.Draw(im_dot).ellipse((2, 2, 14, 14), fill=(214, 72, 62, int(255 * blink)))
        K.paste_rgba(canvas, np.array(im_dot), 90, 224, 1.0)
        K.paste_rgba(canvas, REC_TAG, 112, 214, 0.90)
        lt = lens_tag(lens)
        K.paste_rgba(canvas, lt, 1002 - lt.shape[1], 215, 0.88)


# ---------------------------------------------------------------- animación de títulos y callouts
def draw_line(canvas: np.ndarray, img: np.ndarray, cx: float, cy: float, local_t: float, t0: float, dur_shot: float, style: str = "rise"):
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


# ---------------------------------------------------------------- GUION TÉCNICO DE 12 PLANOS (15.00 s)
SHOTS = [
    # 01 — HOOK: ECU Macro aguja real penetrando piel + Crash Zoom Pull-Back
    dict(
        t0=0.00, t1=1.20, kind="single",
        plate="plate_v01_macro_aguja.mp4", speed=1.18, offset=0.02,
        cam=K.Camera(z=(1.38, 1.12), c=((0.50, 0.44), (0.50, 0.49)), ease="out", rot=(1.6, 0.0), shake=0.34, seed=1),
        lens="ECU MACRO · 100mm",
        scrim="hero",
        zoom_blur_head=0.46,
        flash_head=(0.24, K.PAPER),
        lines=K.stack([
            ("ESTO NO ES", "mont700", 28, K.BONE_L, 11, 0.06, "rise", "label"),
            ("UN TATUAJE.", "cinzel800", 84, K.PAPER, 4, 0.24, "punch", "display"),
        ], top=1185, block_gap=0.34),
    ),
    # 02 — HOOK PAYOFF: Primer Plano Chiaroscuro de pieza oscura en hombro + Punch Zoom-In
    dict(
        t0=1.20, t1=2.40, kind="single",
        plate="plate_v02_hero_reveal.mp4", speed=1.02, offset=0.00,
        cam=K.Camera(z=(1.05, 1.24), c=((0.48, 0.43), (0.50, 0.41)), ease="ramp", rot=(-1.2, 0.4)),
        lens="PRIMER PLANO · 50mm",
        scrim="lower",
        whip=("x", 22),
        flash_head=(0.14, K.CREAM),
        lines=K.stack([
            ("ES UNA FIRMA.", "cinzel800", 80, K.PAPER, 4, 0.08, "punch", "display"),
            ("ARTE EN LA PIEL  ·  DESDE 2009", "mont600", 23, K.TEAL_L, 7, 0.28, "rise", "label"),
        ], top=1205, block_gap=0.46),
    ),
    # 03 — UBICACIÓN REAL: Vuelo Aéreo FPV Dron San Bernardo -> José Joaquín Pérez 528
    dict(
        t0=2.40, t1=3.60, kind="single",
        plate="plate_v03_dron_aereo.mp4", speed=1.95, offset=0.05,
        cam=K.Camera(
            z=(1.02, 1.28),
            c=((0.50, 0.47), (0.50, 0.54)),
            ease="in",
            tilt=((0.0, 0.0), (0.0, -1.8)),
        ),
        lens="GRAN PLANO AÉREO · DRON 16mm",
        scrim="lower",
        zoom_blur_tail=0.44,
        callout=K.callout_badge("UBICACIÓN OFICIAL", "JOSÉ JOAQUÍN PÉREZ 528"),
        lines=K.stack([
            ("SAN BERNARDO  ·  SANTIAGO", "mont700", 23, K.TEAL_L, 8, 0.08, "rise", "label"),
            ("JOSÉ JOAQUÍN PÉREZ 528", "cinzel800", 54, K.PAPER, 3, 0.22, "rise", "display"),
        ], top=1218, block_gap=0.40),
    ),
    # 04 — FACHADA REAL VERIFICADA: Fotografía callejera real con mural y letrero oficial (528)
    dict(
        t0=3.60, t1=4.50, kind="single",
        plate="plate_p01_fachada_real.jpg",
        cam=K.Camera(
            z=(1.05, 1.21),
            c=((0.49, 0.52), (0.54, 0.45)),
            ease="out",
            tilt=((1.4, 1.6), (0.0, 0.0)),
        ),
        lens="PLANO GENERAL · 24mm",
        scrim="lower",
        zoom_blur_head=0.34,
        lines=K.stack([
            ("DESDE 2009", "cinzel800", 78, K.PAPER, 5, 0.06, "punch", "display"),
            ("JOSÉ JOAQUÍN PÉREZ 528  ·  SAN BERNARDO", "mont600", 21, K.CREAM, 5, 0.20, "rise", "label"),
        ], top=1215, block_gap=0.46),
    ),
    # 05 — TRAVELLING POV: Avance subjetivo gimbal por pasillo y vitrina de joyería
    dict(
        t0=4.50, t1=5.40, kind="single",
        plate="plate_v04_pasillo_pov.mp4", speed=2.05, offset=0.05,
        cam=K.Camera(z=(1.05, 1.20), c=((0.50, 0.50), (0.50, 0.47)), ease="inout"),
        lens="TRAVELLING POV · 24mm GIMBAL",
        scrim="lower",
        whip=("y", 18),
        lines=K.stack([
            ("CRUZA LA PUERTA", "cinzel800", 66, K.PAPER, 4, 0.06, "rise", "display"),
            ("PRIVACIDAD  ·  DISEÑO  ·  RIGOR CLÍNICO", "mont600", 21, K.TEAL_L, 6, 0.20, "rise", "label"),
        ], top=1220, block_gap=0.48),
    ),
    # 06 — AUTORIDAD SANITARIA: Plano Cenital Picado de sesión en cabina Seremi
    dict(
        t0=5.40, t1=6.60, kind="single",
        plate="plate_v05_cabina_cenital.mp4", speed=1.22, offset=0.05,
        cam=K.Camera(z=(1.05, 1.20), c=((0.50, 0.44), (0.50, 0.41)), ease="inout", rot=(-1.8, 0.5)),
        lens="PLANO CENITAL · 35mm",
        scrim="lower",
        callout=K.callout_badge("NORMA SANITARIA", "AUTORIZACIÓN SEREMI"),
        lines=K.stack([
            ("ZONA SEREMI", "cinzel800", 76, K.PAPER, 5, 0.08, "punch", "display"),
            ("CABINA ESTÉRIL  ·  AGUJAS SELLADAS", "mont600", 22, K.CREAM, 6, 0.26, "rise", "label"),
        ], top=1215, block_gap=0.46),
    ),
    # 07 — PROCESO EN VIVO: Ink Wipe Reveal (mano con guante negro revelando tatuaje)
    dict(
        t0=6.60, t1=7.80, kind="single",
        plate="plate_v06_wipe_reveal.mp4", speed=1.35, offset=0.08,
        cam=K.Camera(z=(1.06, 1.22), c=((0.50, 0.47), (0.48, 0.44)), ease="out", shake=0.18, seed=4),
        lens="PPP DETALLE · 85mm",
        scrim="lower",
        whip=("x", 18),
        lines=K.stack([
            ("TRAZO A TRAZO", "cinzel800", 74, K.PAPER, 4, 0.08, "rise", "display"),
            ("SOMBRAS PROFUNDAS  ·  CURADO PERFECTO", "mont600", 21, K.TEAL_L, 5, 0.26, "rise", "label"),
        ], top=1215, block_gap=0.46),
    ),
    # 08 — PORTAFOLIO REALISMO: Doble golpe rítmico (08a Crash Zoom-In -> 08b Pull-Back inverso)
    dict(
        t0=7.80, t1=9.00, kind="dual_cut", split_at=0.60,
        plate_a="plate_p02_lobo_samurai.jpg",
        cam_a=K.Camera(z=(1.04, 1.23), c=((0.50, 0.45), (0.48, 0.42)), ease="out", rot=(-2.0, 0.0)),
        plate_b="plate_p03_hombro_realismo.jpg",
        cam_b=K.Camera(z=(1.25, 1.05), c=((0.52, 0.41), (0.50, 0.45)), ease="out", rot=(1.6, 0.0)),
        lens="DETALLE REALISMO · 50mm",
        scrim="lower",
        whip=("x", 24),
        flash_head=(0.12, K.PAPER),
        lines=K.stack([
            ("PIEZA ÚNICA", "cinzel800", 80, K.PAPER, 5, 0.06, "punch", "display"),
            ("REALISMO BLACK & GREY  ·  SIN PLANTILLAS", "mont600", 21, K.CREAM, 5, 0.22, "rise", "label"),
        ], top=1215, block_gap=0.46),
    ),
    # 09 — PORTAFOLIO VERSATILIDAD: Manga completa Black & Grey + Full Color Anime
    dict(
        t0=9.00, t1=10.20, kind="dual_cut", split_at=0.60,
        plate_a="plate_p04_cristo_manga.jpg",
        cam_a=K.Camera(z=(1.10, 1.22), c=((0.50, 0.56), (0.50, 0.43)), ease="inout"),
        plate_b="plate_p05_color_anime.jpg",
        cam_b=K.Camera(z=(1.05, 1.22), c=((0.52, 0.50), (0.50, 0.44)), ease="out", rot=(-1.4, 0.0)),
        lens="PLANO MANGA & COLOR · 35mm",
        scrim="lower",
        whip=("y", 20),
        lines=K.stack([
            ("DISEÑO AUTORAL", "cinzel800", 68, K.PAPER, 4, 0.06, "punch", "display"),
            ("BLACK & GREY  ·  ORIENTAL  ·  FULL COLOR", "mont600", 21, K.TEAL_L, 5, 0.22, "rise", "label"),
        ], top=1215, block_gap=0.48),
    ),
    # 10 — PIERCING CLÍNICO: Split-Screen Doble Macro con banda central limpia (cero obstrucción de joyas)
    dict(
        t0=10.20, t1=11.40, kind="split",
        top_plate="plate_p06_helix_titanio.jpg",
        bot_plate="plate_p07_septum_titanio.jpg",
        top_cam=K.Camera(z=(1.22, 1.06), c=((0.52, 0.44), (0.50, 0.46)), ease="out"),
        bot_cam=K.Camera(z=(1.06, 1.22), c=((0.47, 0.57), (0.45, 0.55)), ease="out"),
        lens="DOBLE MACRO · 100mm",
        whip=("x", 22),
        lines=K.stack([
            ("TITANIO ASTM F136", "cinzel800", 60, K.PAPER, 4, 0.06, "punch", "display", False),
            ("PIERCING CLÍNICO  ·  GRADO IMPLANTE", "mont700", 20, K.TEAL_L, 6, 0.20, "rise", "label", False),
        ], top=904, block_gap=0.45),
    ),
    # 11 — EQUIPO RESIDENTE: Plano Medio Lateral en cabina real + Riser sonoro hacia el CTA
    dict(
        t0=11.40, t1=12.60, kind="single",
        plate="plate_v07_artista_sesion.mp4", speed=1.22, offset=0.10,
        cam=K.Camera(z=(1.04, 1.20), c=((0.48, 0.44), (0.46, 0.40)), ease="inout"),
        lens="PLANO MEDIO · 50mm",
        scrim="lower",
        whip=("x", 18),
        lines=K.stack([
            ("5 ARTISTAS", "cinzel800", 82, K.PAPER, 5, 0.06, "punch", "display"),
            ("UN MISMO ESTÁNDAR DE EXCELENCIA", "mont600", 22, K.CREAM, 6, 0.24, "rise", "label"),
        ], top=1215, block_gap=0.46),
    ),
    # 12 — PACKSHOT / END CARD CTA DE ALTA CONVERSIÓN (2.40 s completos)
    dict(
        t0=12.60, t1=15.00, kind="cta",
        lens="ABYSS  ·  J. J. PÉREZ 528",
    ),
]


# ---------------------------------------------------------------- elementos del Packshot CTA (12.60 – 15.00 s)
EMBLEM = K.load_rgba(os.path.join(PLATES, "emblema_abyss_alpha.png"), (310, 310))
CTA_GLOW = K.glow(480, K.TEAL, 82.0)
CTA_RINGS = K.concentric_rings(780, rings=8, color=K.BONE, max_alpha=30)
CTA_DIV = K.divider(520, K.BONE, K.TEAL_L, 215, r=8)
CTA_PILL = K.pill(
    "WHATSAPP  +56 9 4778 6839",
    "mont800",
    30,
    4,
    fg=K.OBSIDIAN,
    bg=K.PAPER,
    border=K.BONE_L,
    pad_x=44,
    pad_y=23,
    with_diamond=True,
    diamond_color=K.SAGE,
)
CTA_TITLE = K.tracked_text("AGENDA TU HORA", K.font("cinzel800", 72), K.PAPER, 5, shadow=True)
CTA_SUB = K.tracked_text("TATUAJES & PIERCING  ·  DESDE 2009", K.font("mont600", 22), K.BONE_L, 7, shadow=True)
CTA_HANDLE = K.tracked_text("@abyss_tattoo_studio", K.font("mont700", 27), K.CREAM, 4, shadow=True)
CTA_ADDR = K.pill(
    "JOSÉ JOAQUÍN PÉREZ 528  ·  SAN BERNARDO",
    "mont700",
    19,
    4,
    fg=K.TEAL_L,
    bg=(24, 20, 17),
    border=K.SAGE,
    pad_x=28,
    pad_y=12,
    with_diamond=False,
)
CTA_HOURS = K.tracked_text("LUN A DOM · 10:00 A 20:00 HRS  ·  COTIZA TU IDEA HOY", K.font("mont500", 18), K.BONE, 5, shadow=False)

# Fondo atmosférico desenfocado en Obsidiana a partir de la fotografía real de fachada
_bg_src = cv2.GaussianBlur(load_still_rgb("plate_p01_fachada_real.jpg"), (0, 0), 34)
CTA_BG_BASE = np.clip(_bg_src.astype(np.float32) * 0.14 + np.array(K.OBSIDIAN, np.float32) * 0.90, 0, 255).astype(np.uint8)


def render_cta(local_t: float, dur: float) -> np.ndarray:
    p = local_t / dur
    z, cx, cy, *_ = K.Camera(z=(1.04, 1.12), c=((0.50, 0.48), (0.50, 0.46)), ease="out").state(p)
    canvas = K.render_camera(CTA_BG_BASE, z, cx, cy)

    # Halo radial Salvia/Teal + anillos concéntricos grabados
    g_alpha = 0.72 + 0.18 * np.sin(local_t * 2.2)
    K.paste_rgba(canvas, CTA_GLOW, center=True, y=455 - CTA_GLOW.shape[0] // 2, alpha=g_alpha * K.clamp01(local_t / 0.35))
    K.paste_rgba(canvas, CTA_RINGS, center=True, y=455 - CTA_RINGS.shape[0] // 2, alpha=0.85 * K.clamp01(local_t / 0.5))

    # Emblema oficial circular con settle elástico
    tin = K.clamp01(local_t / 0.42)
    sc = 0.85 + 0.15 * K.ease_out_back(tin, 1.35)
    ew = max(2, int(round(EMBLEM.shape[1] * sc)))
    eh = max(2, int(round(EMBLEM.shape[0] * sc)))
    emb = cv2.resize(EMBLEM, (ew, eh), interpolation=cv2.INTER_LINEAR)
    K.paste_rgba(canvas, emb, 540 - ew // 2, 455 - eh // 2, K.ease_out_cubic(tin))

    # Jerarquía tipográfica de conversión (100 % dentro de zona segura Meta/Instagram Reels)
    draw_line(canvas, CTA_TITLE, 540, 706, local_t, 0.16, dur, "punch")
    draw_line(canvas, CTA_SUB, 540, 796, local_t, 0.30, dur, "hold")
    K.paste_rgba(canvas, CTA_DIV, 540 - CTA_DIV.shape[1] // 2, 858 - CTA_DIV.shape[0] // 2, K.clamp01((local_t - 0.42) / 0.26))

    # Botón CTA principal con pop elástico + barrido especular diagonal (shimmer)
    if local_t >= 0.52:
        bt = K.clamp01((local_t - 0.52) / 0.30)
        bsc = 0.88 + 0.12 * K.ease_out_back(bt, 1.55)
        bw = max(2, int(round(CTA_PILL.shape[1] * bsc)))
        bh = max(2, int(round(CTA_PILL.shape[0] * bsc)))
        pill_im = cv2.resize(CTA_PILL, (bw, bh), interpolation=cv2.INTER_LINEAR)
        shimmer_p = (local_t - 0.80) / 0.85 if 0.80 <= local_t <= 1.65 else -1.0
        K.paste_rgba_shimmer(canvas, pill_im, 540, 958, K.ease_out_cubic(bt), shimmer_p)

    draw_line(canvas, CTA_HANDLE, 540, 1076, local_t, 0.72, dur, "hold")
    draw_line(canvas, CTA_ADDR, 540, 1154, local_t, 0.82, dur, "hold")
    draw_line(canvas, CTA_HOURS, 540, 1234, local_t, 0.92, dur, "hold")

    # Flash inicial de impacto en t = 12.60 s
    if local_t < 0.16:
        canvas = K.flash_frame(canvas, 0.32 * (1.0 - local_t / 0.16) ** 2.0, K.PAPER)

    hud_overlay(canvas, 12.60 + local_t, "ABYSS · J. J. PÉREZ 528", soft=True)

    # Loop suave en los últimos 0.20 s para enganche continuo al repetir el Reel
    if dur - local_t < 0.20:
        fade = 0.45 * (1.0 - (dur - local_t) / 0.20) ** 2.0
        canvas = K.flash_frame(canvas, fade, K.OBSIDIAN)
    return canvas


def render_split(sh: dict, local_t: float, dur: float) -> np.ndarray:
    """Split-screen 1080x1920 con dos viewports dedicados 1080x868 y banda central limpia en Obsidiana."""
    p = local_t / dur
    canvas = np.zeros((K.H, K.W, 3), dtype=np.uint8)
    band_top, band_bot = 866, 1054
    vh_top = band_top
    vh_bot = K.H - band_bot

    zt, cxt, cyt, rott, txt, tyt = sh["top_cam"].state(p)
    top_view = K.render_camera(sample_plate(sh["top_plate"], local_t), zt, cxt, cyt, rott, txt, tyt, out_w=K.W, out_h=vh_top)
    zb, cxb, cyb, rotb, txb, tyb = sh["bot_cam"].state(p)
    bot_view = K.render_camera(sample_plate(sh["bot_plate"], local_t), zb, cxb, cyb, rotb, txb, tyb, out_w=K.W, out_h=vh_bot)

    canvas[:band_top] = top_view
    canvas[band_bot:] = bot_view
    canvas[band_top:band_bot] = np.array(K.OBSIDIAN, dtype=np.uint8)

    # Filetes dobles y rombos laterales en la banda central
    im = Image.fromarray(canvas)
    d = ImageDraw.Draw(im)
    d.line([(0, band_top), (K.W, band_top)], fill=K.BONE, width=3)
    d.line([(0, band_bot), (K.W, band_bot)], fill=K.BONE, width=3)
    d.line([(64, band_top + 10), (1016, band_top + 10)], fill=K.SAGE, width=1)
    d.line([(64, band_bot - 10), (1016, band_bot - 10)], fill=K.SAGE, width=1)
    K.diamond(d, 96, (band_top + band_bot) // 2, 8, K.TEAL_L, 255)
    K.diamond(d, K.W - 96, (band_top + band_bot) // 2, 8, K.TEAL_L, 255)
    return np.array(im)


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
        canvas = render_cta(local_t, dur)
        return K.finish_fast(canvas, VIGNETTE_U16, GRAINS_I16[idx % len(GRAINS_I16)])

    if kind == "split":
        canvas = render_split(sh, local_t, dur)
    elif kind == "dual_cut":
        split_at = sh["split_at"]
        if local_t < split_at:
            sub_p = local_t / split_at
            src = sample_plate(sh["plate_a"], local_t)
            z, cx, cy, rot, tx, ty = sh["cam_a"].state(sub_p)
        else:
            sub_p = (local_t - split_at) / (dur - split_at)
            src = sample_plate(sh["plate_b"], local_t - split_at)
            z, cx, cy, rot, tx, ty = sh["cam_b"].state(sub_p)
        canvas = K.render_camera(src, z, cx, cy, rot, tx, ty)
        if abs(local_t - split_at) < 0.09:
            canvas = K.flash_frame(canvas, 0.22 * (1.0 - abs(local_t - split_at) / 0.09) ** 2.0, K.CREAM)
    else:
        src = sample_plate(sh["plate"], local_t, sh.get("speed", 1.0), sh.get("offset", 0.0))
        z, cx, cy, rot, tx, ty = sh["cam"].state(p)
        canvas = K.render_camera(src, z, cx, cy, rot, tx, ty)

    # Desenfoques ópticos de tiro de cámara (whip pan / radial dive blur)
    if "whip" in sh:
        axis, amt = sh["whip"]
        w_env = whip_envelope(local_t, dur)
        if w_env > 0.03:
            canvas = K.motion_blur(canvas, amt * w_env, 0.0 if axis == "x" else 90.0)

    if "zoom_blur_head" in sh and local_t < 0.24:
        canvas = K.radial_zoom_blur(canvas, sh["zoom_blur_head"] * (1.0 - local_t / 0.24) ** 1.8)
    if "zoom_blur_tail" in sh and (dur - local_t) < 0.24:
        canvas = K.radial_zoom_blur(canvas, sh["zoom_blur_tail"] * (1.0 - (dur - local_t) / 0.24) ** 1.8)

    # Scrim editorial de contraste para legibilidad 100 % sin tapar el arte superior
    if kind != "split":
        scrim_lut = SCRIM_HERO if sh.get("scrim") == "hero" else SCRIM_LOWER
        canvas = K.apply_scrim_fast(canvas, scrim_lut)

    # Callout HUD técnico estilo Solen cuando corresponde
    if "callout" in sh and local_t > 0.10:
        cb = sh["callout"]
        tin_c = K.clamp01((local_t - 0.10) / 0.24) * K.clamp01((dur - local_t) / 0.15)
        K.paste_rgba(canvas, cb, 86, 276, tin_c)

    # Tipografía cinética
    for (img, lx, ly, t0, style) in sh.get("lines", []):
        draw_line(canvas, img, lx, ly, local_t, t0, dur, style)

    if "flash_head" in sh and local_t < 0.12:
        amt, tint = sh["flash_head"]
        canvas = K.flash_frame(canvas, amt * (1.0 - local_t / 0.12) ** 2.0, tint)

    hud_overlay(canvas, t, sh["lens"])
    return K.finish_fast(canvas, VIGNETTE_U16, GRAINS_I16[idx % len(GRAINS_I16)])


def encode():
    os.makedirs("film", exist_ok=True)
    # 1. Máster Social 1080x1920 @ 60 fps (~14-16 Mbps H.264 High BT.709, óptimo para Instagram Reels / TikTok / Meta Ads)
    cmd_social = [
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
        "-movflags", "+faststart", "-shortest",
        OUT_SOCIAL,
    ]
    log_f = open("/tmp/ff_social.log", "wb")
    proc = subprocess.Popen(cmd_social, stdin=subprocess.PIPE, stderr=log_f)
    for i in range(N):
        f = render_frame(i)
        proc.stdin.write(f.tobytes())
        if i == 34:  # t = 0.57 s — portada de gancho (Hook)
            Image.fromarray(f).save(COVER_HOOK, quality=94)
        if i == 858:  # t = 14.30 s — póster CTA completo estabilizado
            Image.fromarray(f).save(POSTER_CTA, quality=95)
        if (i + 1) % 150 == 0 or i == N - 1:
            print(f"  renderizado {i + 1}/{N} frames  ({(i + 1) / FPS:.1f}s)", flush=True)
    proc.stdin.close()
    rc = proc.wait()
    log_f.close()
    if rc != 0:
        raise RuntimeError(open("/tmp/ff_social.log", "rb").read().decode(errors="ignore")[-2000:])
    print(f"Máster Social 60fps -> {OUT_SOCIAL}")

    # 2. Derivada Web / WhatsApp 1080x1920 @ 30 fps (~5.5 Mbps CRF 21)
    subprocess.run(
        [
            FFMPEG, "-y", "-i", OUT_SOCIAL,
            "-vf", "fps=30",
            "-c:v", "libx264", "-preset", "medium", "-crf", "21",
            "-profile:v", "high", "-pix_fmt", "yuv420p",
            "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
            "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart",
            OUT_WEB,
        ],
        check=True,
        stderr=subprocess.DEVNULL,
    )
    print(f"Derivada Web 30fps  -> {OUT_WEB}")


if __name__ == "__main__":
    encode()
