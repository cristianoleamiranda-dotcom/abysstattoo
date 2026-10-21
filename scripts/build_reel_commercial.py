#!/usr/bin/env python3
"""
build_reel_commercial.py — Monta el Reel Comercial de 15 s de Abyss Tattoo Studio.

Estructura comercial (pulsada a 100 BPM, cortes cada 0.60 s):
  0.00–2.40  HOOK        macro de aguja + zoom de impacto sobre la obra (promesa)
  2.40–7.80  CONTEXTO    fachada, pasillo, cabina clínica, macro de sombreado (autoridad)
  7.80–11.40 PRUEBA      portafolio, diseño autoral y piercing de titanio (resultado)
  11.40–12.60 EQUIPO     artistas en sesión
  12.60–15.00 CTA        emblema + WhatsApp + dirección + usuario (una sola acción)

Uso:
  python scripts/build_reel_commercial.py            # máster 1080x1920 60 fps -> film/
  python scripts/build_reel_commercial.py --fps 30   # variante social
  python scripts/build_reel_commercial.py --preview  # 540x960, 3 s, para revisar rápido
"""

import argparse
import math
import os
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import reel_kit as K
from reel_kit import (BONE, BONE_L, CREAM, OBSIDIAN, PANEL, PAPER, SAGE, TEAL, TEAL_L)

ROOT = "/home/user/abysstattoo"
os.chdir(ROOT)
FFMPEG = f"{ROOT}/.venv/bin/ffmpeg"
PLATES = "assets/reel_plates"
TOTAL = 15.0

# --------------------------------------------------------------------------- lector de placas
class Reader:
    def __init__(self, path):
        self.path = path
        self.cap = cv2.VideoCapture(path)
        self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 30.0
        self.n = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.pos = -10
        self.still = None

    def frame(self, t):
        if self.still is not None:
            return self.still
        idx = max(0, min(self.n - 1, int(round(t * self.fps))))
        if idx != self.pos + 1:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ok, fr = self.cap.read()
        if not ok:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, idx - 1))
            ok, fr = self.cap.read()
        self.pos = idx
        return cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)


def still_reader(path):
    r = Reader.__new__(Reader)
    r.still = cv2.cvtColor(cv2.imread(path), cv2.COLOR_BGR2RGB)
    return r


# --------------------------------------------------------------------------- elementos gráficos
class El:
    """Elemento gráfico animado: aparición por máscara, ascenso, pop o barrido lateral."""

    def __init__(self, img, cx=None, cy=None, x=None, y=None, t0=0.0, dur=0.42,
                 style="rise", ease="out", dy=34, dx=0, alpha=1.0):
        self.img = img
        self.cx, self.cy, self.x, self.y = cx, cy, x, y
        self.t0, self.dur, self.style, self.ease = t0, dur, style, ease
        self.dy, self.dx, self.base_alpha = dy, dx, alpha

    def draw(self, canvas, t):
        p = K.clamp01((t - self.t0) / max(self.dur, 1e-4))
        if p <= 0:
            return
        e = K.EASES[self.ease](p)
        a = self.base_alpha * min(1.0, p * 2.6)
        img = self.img
        oy = ox = 0
        if self.style == "rise":
            oy = (1 - e) * self.dy
        elif self.style == "slide":
            ox = (1 - e) * self.dx
        elif self.style == "pop":
            a = self.base_alpha * min(1.0, p * 3.2)
        elif self.style == "mask":
            h = img.shape[0]
            cut = int(h * (1 - e))
            if cut >= h:
                return
            img = img.copy()
            img[:cut, :, 3] = 0
        if self.x is not None and self.y is not None and self.cx is None:
            x, y = self.x + ox, self.y + oy
        else:
            cx = self.cx if self.cx is not None else K.W / 2
            cy = self.cy if self.cy is not None else K.H / 2
            x = cx - img.shape[1] / 2 + ox
            y = cy - img.shape[0] / 2 + oy
        K.paste_rgba(canvas, img, x, y, a)


# --------------------------------------------------------------------------- gráficos precargados
def build_assets():
    a = {}
    a["corner"] = K.corner_hud(alpha=132)
    a["emblem"] = K.load_rgba(f"{PLATES}/emblema_abyss_alpha.png", (330, 330))
    a["glow"] = K.glow(320, TEAL_L, 62)
    a["micro_hud"] = K.tracked_text("ABYSS TATTOO STUDIO  ·  SAN BERNARDO  ·  DESDE 2009",
                                    K.font("mont600", 21), BONE_L, 5)
    a["rec"] = K.tracked_text("REC", K.font("mont700", 20), BONE_L, 5)
    a["dots"] = []
    for i in range(0, 10):
        a["dots"].append(K.tracked_text(f"00:0{i}:{i * 3:02d}", K.font("mont600", 20), BONE, 3))
    a["tc_cache"] = {}
    return a


def tc_img(assets, t):
    key = int(t * 10) / 10.0
    if key not in assets["tc_cache"]:
        s = int(t)
        f = int(round((t - s) * 30))
        assets["tc_cache"][key] = K.tracked_text(f"00:00:{s:02d}:{f:02d}", K.font("mont600", 20), BONE, 3)
    return assets["tc_cache"][key]


# --------------------------------------------------------------------------- línea de tiempo
def make_timeline():
    Cam = K.Camera
    shots = [
        dict(id="01", t0=0.00, dur=1.20, code="ECU · 85mm MACRO", src=("vid", f"{PLATES}/plate_v03_macro.mp4"),
             tin=0.36, speed=0.85,
             cam=Cam(z=(1.34, 1.12), c=((0.50, 0.55), (0.52, 0.51)), ease="out", shake=0.30, seed=1),
             fx=dict(fade_in=0.12, blur_in=16, angle=90, scrim="text", flash=0.0)),
        dict(id="02", t0=1.20, dur=1.20, code="PRIMER PLANO · 50mm", src=("still", f"{PLATES}/plate_p02_lobo.jpg"),
             cam=Cam(z=(1.02, 1.24), c=((0.50, 0.46), (0.52, 0.44)), ease="out", shake=0.12, seed=2),
             fx=dict(blur_in=26, angle=0, scrim="text", flash=0.14)),
        dict(id="03", t0=2.40, dur=1.80, code="PLANO GENERAL · 24mm", src=("still", f"{PLATES}/plate_s03_fachada_dia.jpg"),
             cam=Cam(z=(1.04, 1.16), c=((0.50, 0.52), (0.50, 0.49)), ease="linear", shake=0.08, seed=3),
             fx=dict(blur_in=30, angle=0, scrim="text", flash=0.0)),
        dict(id="04", t0=4.20, dur=1.20, code="TRAVELLING · 35mm", src=("still", f"{PLATES}/plate_s04_pasillo.jpg"),
             cam=Cam(z=(1.06, 1.30), c=((0.50, 0.47), (0.50, 0.50)), ease="out", shake=0.10, seed=4),
             fx=dict(blur_in=22, angle=90, scrim="text", flash=0.0)),
        dict(id="05", t0=5.40, dur=1.20, code="PLANO MEDIO · 35mm", src=("vid", f"{PLATES}/plate_v02_cabina.mp4"),
             tin=0.06, speed=0.9,
             cam=Cam(z=(1.08, 1.16), c=((0.50, 0.48), (0.52, 0.52)), ease="linear", shake=0.16, seed=5),
             fx=dict(blur_in=16, angle=0, scrim="text", flash=0.0)),
        dict(id="06", t0=6.60, dur=1.20, code="MACRO · 100mm", src=("vid", f"{PLATES}/plate_v04_sombreado.mp4"),
             tin=0.20, speed=1.0,
             cam=Cam(z=(1.05, 1.20), c=((0.48, 0.50), (0.52, 0.48)), ease="out", shake=0.20, seed=6),
             fx=dict(blur_in=20, angle=0, scrim="text", flash=0.12)),
        dict(id="07", t0=7.80, dur=1.20, code="PLANO DETALLE · 50mm", src=("still", f"{PLATES}/plate_p03_hombro.jpg"),
             cam=Cam(z=(1.20, 1.06), c=((0.52, 0.44), (0.49, 0.47)), ease="out", rot=(-1.6, 0.0), shake=0.10, seed=7),
             fx=dict(blur_in=34, angle=0, scrim="text", flash=0.0)),
        dict(id="08", t0=9.00, dur=1.20, code="PLANO AMERICANO · 35mm", src=("still", f"{PLATES}/plate_p04_cristo.jpg"),
             cam=Cam(z=(1.06, 1.18), c=((0.50, 0.48), (0.51, 0.46)), ease="linear", rot=(0.6, -0.6), shake=0.14, seed=8),
             fx=dict(blur_in=20, angle=0, scrim="text", flash=0.10)),
        dict(id="09", t0=10.20, dur=1.20, code="DOS PLANOS · 100mm", src=("split", f"{PLATES}/plate_p06_helix.jpg",
                                                                    f"{PLATES}/plate_p07_septum.jpg"),
             cam=Cam(z=(1.14, 1.04), c=((0.50, 0.50), (0.50, 0.50)), ease="out", shake=0.06, seed=9),
             fx=dict(blur_in=18, angle=90, scrim="text", split=True, flash=0.0)),
        dict(id="10", t0=11.40, dur=1.20, code="MEDIO · 35mm", src=("vid", f"{PLATES}/plate_v06_sesion.mp4"),
             tin=0.20, speed=1.0,
             cam=Cam(z=(1.10, 1.22), c=((0.48, 0.48), (0.50, 0.50)), ease="out", shake=0.14, seed=10),
             fx=dict(blur_in=28, angle=270, scrim="text", flash=0.0)),
        dict(id="11", t0=12.60, dur=2.40, code="CIERRE", src=("still", f"{PLATES}/plate_s02_fachada_noche.jpg"),
             cam=Cam(z=(1.22, 1.06), c=((0.50, 0.50), (0.50, 0.50)), ease="out", shake=0.0, seed=11),
             fx=dict(blur_in=0, angle=0, scrim="text", flash=0.0, dark=0.62, darkblur=9, fade_in=0.30)),
    ]
    return shots


# --------------------------------------------------------------------------- copies por plano
def els(items, alpha=1.0):
    """Convierte el stack tipográfico en elementos gráficos listos para dibujar."""
    out = []
    for img, y, t0, style in items:
        out.append(El(img, cx=K.W / 2, cy=y + img.shape[0] / 2, t0=t0, dur=0.40, style=style, alpha=alpha))
    return out


def eyebrow(text, color=TEAL_L):
    return K.tracked_text(text, K.font("mont600", 25), color, 11)


def build_graphics(A):
    G = {}
    mid, mid2 = 0.55, 0.14

    G["01"] = els(K.stack([
        ("ESTO NO ES", "mont500", 34, BONE_L, 14, 0.06, "mask", "sub"),
        ("UN TATUAJE.", "cinzel800", 116, PAPER, 2, 0.16, "mask", "display"),
        ("ES UNA FIRMA.", "cinzel700", 58, TEAL_L, 8, 0.52, "mask", "display"),
    ], top=690))

    G["02"] = els(K.stack([
        ("ES UNA FIRMA.", "cinzel800", 104, PAPER, 2, 0.02, "mask", "display"),
        ("REALISMO BLACK & GREY", "mont600", 27, BONE_L, 10, 0.18, "mask", "sub"),
    ], top=760))

    G["03"] = els(K.stack([
        ("SAN BERNARDO · CHILE", "mont500", 26, BONE_L, 10, 0.14, "mask", "sub"),
        ("DESDE 2009", "cinzel800", 104, PAPER, 3, 0.24, "mask", "display"),
        ("JOSÉ JOAQUÍN PÉREZ 528", "mont600", 27, BONE_L, 5, 0.38, "mask", "sub"),
    ], top=940))

    G["04"] = els(K.stack([
        ("ENTRA.", "cinzel800", 132, PAPER, 4, 0.04, "mask", "display"),
        ("UN ESTUDIO, NO UNA VITRINA.", "mont600", 25, BONE_L, 7, 0.22, "mask", "sub"),
    ], top=930))

    G["05"] = els(K.stack([
        ("CABINA CLÍNICA", "cinzel800", 88, PAPER, 3, 0.03, "mask", "display"),
        ("AGUJAS SELLADAS · PROTOCOLO SEREMI", "mont600", 23, BONE_L, 5, 0.18, "mask", "sub"),
    ], top=940))

    G["06"] = els(K.stack([
        ("REALISMO", "cinzel800", 106, PAPER, 3, 0.03, "mask", "display"),
        ("BLACK & GREY", "mont600", 40, BONE_L, 18, 0.16, "mask", "sub"),
    ], top=900))

    G["07"] = els(K.stack([
        ("PIEZA ÚNICA", "cinzel800", 96, PAPER, 3, 0.05, "mask", "display"),
        ("DISEÑO PERSONALIZADO SIN PLANTILLAS", "mont600", 22, BONE_L, 6, 0.20, "mask", "sub"),
    ], top=950))

    G["08"] = els(K.stack([
        ("SIN PLANTILLAS", "cinzel800", 92, PAPER, 3, 0.04, "mask", "display"),
        ("CADA PIEZA SE DISEÑA PARA TI", "mont600", 24, BONE_L, 7, 0.18, "mask", "sub"),
    ], top=950))

    G["09"] = els(K.stack([
        ("TITANIO", "cinzel800", 88, PAPER, 9, 0.05, "mask", "display"),
        ("ASTM F136 · GRADO IMPLANTE", "mont600", 24, TEAL_L, 6, 0.18, "mask", "sub"),
    ], top=684)) + els(K.stack([
        ("PERFORACIÓN CLÍNICA", "cinzel700", 50, PAPER, 6, 0.30, "mask", "display"),
    ], top=1150))

    G["10"] = els(K.stack([
        ("5 ARTISTAS", "cinzel800", 100, PAPER, 3, 0.03, "mask", "display"),
        ("UN MISMO ESTÁNDAR", "mont600", 28, BONE_L, 10, 0.18, "mask", "sub"),
    ], top=930))

    # ---------------- cierre + CTA (zona segura 9:16)
    cta = [
        El(A["glow"], cx=540, cy=596, t0=0.10, dur=0.60, ease="out"),
        El(A["emblem"], cx=540, cy=596, t0=0.12, dur=0.55, style="pop", ease="back"),
    ]
    cta += els(K.stack([
        ("AGENDA TU HORA", "cinzel800", 80, PAPER, 5, 0.34, "mask", "display"),
        ("TATUAJES & PIERCING · DESDE 2009", "mont500", 22, BONE_L, 6, 0.46, "mask", "sub"),
    ], top=800))
    cta += [
        El(K.divider(560, BONE, TEAL_L, 205), cx=540, cy=1010, t0=0.56, dur=0.40),
        El(K.pill("WHATSAPP  +56 9 4778 6839", "mont700", 34, 3, OBSIDIAN, PAPER,
                  border=None, pad_x=44, pad_y=26, diamond_color=SAGE), cx=540, cy=1092,
           t0=0.64, dur=0.42, style="pop"),
    ]
    cta += els(K.stack([
        ("@abyss_tattoo_studio", "mont700", 33, TEAL_L, 2, 0.78, "mask", "display"),
        ("JOSÉ JOAQUÍN PÉREZ 528 · SAN BERNARDO", "mont600", 25, BONE_L, 4, 0.90, "mask", "sub"),
    ], top=1180))
    cta += els(K.stack([
        ("ESCRIBE Y COORDINAMOS TU HORA", "mont600", 22, TEAL_L, 7, 1.05, "mask", "sub"),
    ], top=1310))
    G["11"] = cta
    return G


# --------------------------------------------------------------------------- cierre
def make_closing_bg():
    """Fondo del cierre: mural del estudio desenfocado + degradado obsidiana, sin ruido amarillo."""
    mural = cv2.cvtColor(cv2.imread("assets/estudio/fachada.jpg"), cv2.COLOR_BGR2RGB)
    z, cx, cy, _ = K.Camera(z=(1.05, 1.05), c=((0.5, 0.5), (0.5, 0.5)), ease="out").state(0.0)
    base = K.crop_window(mural, 1.30, K.OVW * 0.30, K.OVH * 0.52)
    base = cv2.GaussianBlur(base, (0, 0), 26).astype(np.float32)
    gray = (0.299 * base[..., 0] + 0.587 * base[..., 1] + 0.114 * base[..., 2])[..., None]
    base = gray * 0.55 + base * 0.45
    # teal en sombras + hueso en luces
    lum = gray / 255.0
    base = base * (0.55 + 0.45 * lum)
    base[..., 1] += (1 - lum[..., 0]) * 8
    base[..., 2] -= (1 - lum[..., 0]) * 6
    base = base * 0.30 + np.array(K.OBSIDIAN, np.float32) * 0.70

    # degradado vertical de base
    yy = np.linspace(0, 1, K.H, dtype=np.float32)[:, None, None]
    grad = np.array(K.OBSIDIAN, np.float32) * (1 - yy) + np.array((12, 10, 9), np.float32) * yy
    out = grad + base * 0.85

    # viñeta radial hacia el emblema
    YY, XX = np.mgrid[0:K.H, 0:K.W].astype(np.float32)
    r = np.sqrt(((XX - K.W / 2) / (K.W * 0.95)) ** 2 + ((YY - K.H * 0.40) / (K.H * 0.72)) ** 2)
    out *= np.clip(1.06 - r ** 1.9, 0.10, 1.0)[..., None]
    return np.clip(out, 0, 255).astype(np.uint8)


def blend_closing(sharper, closing_bg):
    """Mezcla el fondo del cierre manteniendo una insinuación de la fachada en movimiento."""
    out = closing_bg.astype(np.float32) * 0.88 + sharper.astype(np.float32) * 0.12
    return np.clip(out, 0, 255).astype(np.uint8)


def split_divider(img, y=K.H // 2):
    """Línea de separación del split screen con rombo central (verde salvia)."""
    out = img.copy()
    out[y - 1:y + 1] = np.array(K.TEAL, np.uint8)
    pil = Image.fromarray(out)
    d = ImageDraw.Draw(pil, "RGBA")
    cx, cy, r = K.W // 2, y, 13
    d.polygon([(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)], fill=K.TEAL + (255,))
    d.rectangle((cx - 34, y - 1, cx - 20, y + 1), fill=K.TEAL + (200,))
    d.rectangle((cx + 20, y - 1, cx + 34, y + 1), fill=K.TEAL + (200,))
    return np.array(pil)


# --------------------------------------------------------------------------- scrims
def scrim(img, mode):
    if mode == "bottom":
        h = img.shape[0]
        g = np.linspace(0, 1, h) ** 2.1
        mask = np.clip((g - 0.32) / 0.68, 0, 1)[:, None, None]
        return np.clip(img.astype(np.float32) * (1 - 0.62 * mask), 0, 255).astype(np.uint8)
    if mode == "band":
        out = img.astype(np.float32)
        y0, y1 = 862, 1102
        out[y0:y1] *= 0.16
        edge = 26
        for i in range(edge):
            f = 0.16 + (i / edge) * 0.84
            out[y0 - edge + i] *= f
            out[y1 + i - 1] *= f
        return np.clip(out, 0, 255).astype(np.uint8)
    if mode == "text":
        img = K.text_scrim(img, 580, 1500, 0.52)
        return scrim(img, "bottom")
    if mode == "full":
        return img
    return img


# --------------------------------------------------------------------------- render
def render(fps=60, out="film/reel_comercial_abyss_15s.mp4", preview=False, audio=None, scale=1.0):
    shots = make_timeline()
    A = build_assets()
    G = build_graphics(A)
    closing_bg = make_closing_bg()
    vmap = K.make_vignette(0.46, 2.15)
    grain = K.make_grain_tiles(10, 5.2)

    readers = {}
    for s in shots:
        kind = s["src"][0]
        if kind == "vid":
            readers[s["id"]] = Reader(s["src"][1])
        elif kind == "still":
            readers[s["id"]] = still_reader(s["src"][1])
        else:
            readers[s["id"]] = (still_reader(s["src"][1]), still_reader(s["src"][2]))

    ow = int(round(K.W * scale / 2.0)) * 2
    oh = int(round(K.H * scale / 2.0)) * 2
    n_frames = int(round(TOTAL * fps))
    if preview:
        n_frames = min(n_frames, int(4.0 * fps))

    cmd = [FFMPEG, "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{ow}x{oh}", "-r", str(fps), "-i", "-"]
    if audio:
        cmd += ["-i", audio]
    cmd += ["-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p",
            "-profile:v", "high", "-level", "4.2", "-colorspace", "bt709",
            "-color_primaries", "bt709", "-color_trc", "bt709", "-movflags", "+faststart"]
    if audio:
        cmd += ["-c:a", "aac", "-b:a", "192k", "-shortest"]
    cmd += [out]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)

    si = 0
    for fi in range(n_frames):
        t = fi / fps
        while si + 1 < len(shots) and t >= shots[si + 1]["t0"]:
            si += 1
        s = shots[si]
        lt = t - s["t0"]
        p = K.clamp01(lt / s["dur"])
        fx = s["fx"]

        if s["src"][0] == "split":
            r_top, r_bot = readers[s["id"]]
            top = r_top.frame(0)
            bot = r_bot.frame(0)
            z, cx, cy, rot = s["cam"].state(p)
            a = K.crop_window(top, z, cx, cy, rot)
            b = K.crop_window(bot, z + 0.06, cx, cy, -rot)
            img = np.concatenate([a[: K.H // 2], b[K.H // 2:]], axis=0)
            if fx.get("split"):
                img = split_divider(img)
        else:
            r = readers[s["id"]]
            tin = s.get("tin", 0.0) + lt * s.get("speed", 1.0)
            frame = r.frame(tin)
            z, cx, cy, rot = s["cam"].state(p)
            img = K.crop_window(frame, z, cx, cy, rot)

        # whip / motion blur de entrada
        bl = fx.get("blur_in", 0) * max(0.0, 1 - lt / 0.20) ** 1.6
        if bl > 0.6:
            img = K.motion_blur(img, bl, fx.get("angle", 0))

        if s["id"] == "11":
            img = blend_closing(img, closing_bg)

        if fx.get("scrim"):
            img = scrim(img, fx["scrim"])

        # HUD de visor (todos los planos menos el cierre)
        if s["id"] != "11":
            K.paste_rgba(img, A["corner"], 0, 0, 1.0)
            K.paste_rgba(img, K.tracked_text(s["code"], K.font("mont700", 20), TEAL_L, 5), 96, 232, 0.85)
            mh = A["micro_hud"]
            K.paste_rgba(img, mh, (K.W - mh.shape[1]) // 2, 1442, 0.5)
            tc = tc_img(A, t)
            K.paste_rgba(img, tc, 1016 - tc.shape[1], 232, 0.8)
            K.paste_rgba(img, A["rec"], 1016 - tc.shape[1] - 74, 232, 0.8)
            if int(t * 2) % 2 == 0:
                dot = np.zeros((12, 12, 4), np.uint8)
                dot[..., 0], dot[..., 1], dot[..., 2], dot[..., 3] = 210, 96, 82, 255
                K.paste_rgba(img, dot, 1016 - tc.shape[1] - 90, 240, 0.95)

        # textos del plano
        for el in G.get(s["id"], []):
            el.draw(img, t)

        # flashes de corte
        fl = fx.get("flash", 0.0) * max(0.0, 1 - lt / 0.09)
        if fl > 0.01:
            img = K.flash_frame(img, fl)

        if fx.get("fade_in"):
            f = K.clamp01(lt / fx["fade_in"])
            if f < 1:
                img = (img.astype(np.float32) * f).astype(np.uint8)

        if s["id"] == "11":
            fade_out = K.clamp01((TOTAL - t) / 0.30)
            if fade_out < 1:
                img = (img.astype(np.float32) * fade_out).astype(np.uint8)

        g = grain[fi % len(grain)]
        img = K.finish(img, vmap, g, 1.0, 0.15, 1.02)
        if scale != 1.0:
            img = cv2.resize(img, (ow, oh), interpolation=cv2.INTER_AREA)

        proc.stdin.write(np.ascontiguousarray(img).tobytes())
        if fi % 60 == 0:
            print(f"  frame {fi}/{n_frames}  t={t:5.2f}s  plano {s['id']}", flush=True)

    proc.stdin.close()
    proc.wait()
    print("Listo:", out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--fps", type=int, default=60)
    ap.add_argument("--out", default="film/reel_comercial_abyss_15s_1080x1920_60fps.mp4")
    ap.add_argument("--audio", default="film/reel_abyss_15s_audio.wav")
    ap.add_argument("--preview", action="store_true")
    args = ap.parse_args()
    if args.preview:
        render(30, "film/_preview_reel.mp4", preview=True, audio=None, scale=0.5)
    else:
        audio = args.audio if os.path.exists(args.audio) else None
        render(args.fps, args.out, audio=audio)
