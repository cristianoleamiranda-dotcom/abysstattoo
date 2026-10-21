#!/usr/bin/env python3
"""
reel_kit.py — Kit de gráficos, cámara virtual y postproducción para el Reel Comercial de Abyss.
Módulos VectorCraft (tipografía/HUD) + FilmCraft (cámara, motion blur, grano, viñeta).
"""

import math

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------- paleta oficial
OBSIDIAN = (20, 16, 13)
PANEL = (26, 21, 18)
BONE = (181, 162, 149)
BONE_L = (198, 183, 171)
CREAM = (234, 227, 221)
PAPER = (246, 241, 237)
SAGE = (85, 108, 101)
TEAL = (108, 146, 138)
TEAL_L = (158, 196, 186)

W, H = 1080, 1920
OVW, OVH = 1296, 2304

FONTS = {
    "cinzel800": "assets/fonts/cinzel-800.ttf",
    "cinzel700": "assets/fonts/cinzel-700.ttf",
    "cinzel600": "assets/fonts/cinzel-600.ttf",
    "mont800": "assets/fonts/montserrat-800.ttf",
    "mont700": "assets/fonts/montserrat-700.ttf",
    "mont600": "assets/fonts/montserrat-600.ttf",
    "mont500": "assets/fonts/montserrat-500.ttf",
}
_font_cache = {}


def font(key, size):
    k = (key, size)
    if k not in _font_cache:
        _font_cache[k] = ImageFont.truetype(FONTS[key], size)
    return _font_cache[k]


# ---------------------------------------------------------------- easing
def clamp01(x):
    return 0.0 if x < 0 else (1.0 if x > 1 else x)


def ease_out_quart(p):
    p = clamp01(p)
    return 1 - (1 - p) ** 4


def ease_out_cubic(p):
    p = clamp01(p)
    return 1 - (1 - p) ** 3


def ease_in_cubic(p):
    p = clamp01(p)
    return p ** 3


def ease_in_out_cubic(p):
    p = clamp01(p)
    return 4 * p ** 3 if p < 0.5 else 1 - (-2 * p + 2) ** 3 / 2


def ease_out_back(p, s=1.4):
    p = clamp01(p)
    return 1 + (s + 1) * (p - 1) ** 3 + s * (p - 1) ** 2


EASES = {
    "linear": lambda p: clamp01(p),
    "out": ease_out_quart,
    "outcubic": ease_out_cubic,
    "in": ease_in_cubic,
    "inout": ease_in_out_cubic,
    "back": ease_out_back,
}


# ---------------------------------------------------------------- tipografía
def text_size(text, fnt, tracking=0):
    w = 0
    for ch in text:
        w += fnt.getlength(ch) + tracking
    return int(round(w - tracking)), int(round(fnt.size * 1.36))


def tracked_text(text, fnt, fill, tracking=0, pad=6):
    """Dibuja texto con tracking manual (kerning editorial) en una imagen RGBA ajustada."""
    tw, th = text_size(text, fnt, tracking)
    img = Image.new("RGBA", (tw + pad * 2, th + pad * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    x = pad
    asc, desc = fnt.getmetrics()
    baseline = pad + asc
    for ch in text:
        d.text((x, baseline), ch, font=fnt, fill=fill + (255,), anchor="ls")
        x += fnt.getlength(ch) + tracking
    return np.array(img)


def stack(items, top, display_gap=0.02, block_gap=0.55):
    """Apila copys con alturas reales (sin solapamientos) y devuelve elementos ya posicionados."""
    y = float(top)
    out = []
    prev_kind = None
    for it in items:
        text, fkey, size, color, tracking, t0, style = it[:7]
        kind = it[7] if len(it) > 7 else "line"
        img = tracked_text(text, font(fkey, size), color, tracking)
        if prev_kind == "display" and kind == "display":
            y += size * display_gap
        elif prev_kind is not None:
            y += size * block_gap
        out.append((img, y, t0, style))
        y += img.shape[0]
        prev_kind = kind
    return out


def wrap_lines(lines, fnt_key, size, fill, tracking=0, line_gap=1.02):
    """Apila varias líneas centradas en una sola imagen RGBA."""
    imgs = [tracked_text(l, font(fnt_key, size), fill, tracking) for l in lines]
    w = max(i.shape[1] for i in imgs)
    gap = int(size * 0.30 * line_gap)
    h = sum(i.shape[0] for i in imgs) + gap * (len(imgs) - 1)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    y = 0
    for i in imgs:
        out.paste(Image.fromarray(i), ((w - i.shape[1]) // 2, y), Image.fromarray(i))
        y += i.shape[0] + gap
    return np.array(out)


def diamond(draw, cx, cy, r, fill, alpha=255):
    draw.polygon([(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)], fill=fill + (alpha,))


def line_alpha(draw, pts, fill, width=2, alpha=255):
    draw.line(pts, fill=fill + (alpha,), width=width)


def pill(text, fnt_key, size, tracking, fg, bg, border=None, pad_x=46, pad_y=26,
         with_diamond=True, diamond_color=None):
    fnt = font(fnt_key, size)
    tw, th = text_size(text, fnt, tracking)
    dot = int(size * 0.55)
    extra = int(dot * 1.5) if with_diamond else 0
    w = tw + pad_x * 2 + extra
    h = th + pad_y * 2
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, w - 1, h - 1), radius=h // 2, fill=bg + (255,),
                        outline=(border + (255,)) if border else None, width=2 if border else 1)
    x0 = pad_x
    if with_diamond:
        diamond(d, x0 + dot // 2, h // 2, int(dot * 0.5), diamond_color or fg)
        x0 += extra
    x = x0
    asc, desc = fnt.getmetrics()
    for ch in text:
        d.text((x, h // 2 - th // 2 + asc - 2), ch, font=fnt, fill=fg + (255,))
        x += fnt.getlength(ch) + tracking
    return np.array(img)


def corner_hud(alpha=150, inset=(64, 196, 1016, 1500), length=54, color=BONE, width=2):
    """Escuadras de visor ┌ ┐ └ ┘ dibujadas como líneas vectoriales."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    x0, y0, x1, y1 = inset
    for (cx, cy, sx, sy) in [(x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)]:
        line_alpha(d, [(cx, cy), (cx + sx * length, cy)], color, width, alpha)
        line_alpha(d, [(cx, cy), (cx, cy + sy * length)], color, width, alpha)
    return np.array(img)


def hline(width, color, alpha, thickness=2):
    img = Image.new("RGBA", (width, thickness + 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.line([(0, thickness // 2), (width, thickness // 2)], fill=color + (alpha,), width=thickness)
    return np.array(img)


def divider(width, color_line, color_dot, alpha=220, r=9):
    h = 26
    img = Image.new("RGBA", (width, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cy = h // 2
    gap = r * 3
    d.line([(0, cy), (width // 2 - gap, cy)], fill=color_line + (alpha,), width=2)
    d.line([(width // 2 + gap, cy), (width, cy)], fill=color_line + (alpha,), width=2)
    diamond(d, width // 2, cy, r, color_dot, alpha)
    return np.array(img)


def text_scrim(img, y0=600, y1=1420, strength=0.55):
    """Degradado vertical suave detrás del bloque de copy para asegurar contraste en móvil."""
    h = img.shape[0]
    out = img.astype(np.float32)
    ys = np.arange(h, dtype=np.float32)
    up = np.clip((ys - y0) / 240.0, 0, 1)
    down = np.clip((y1 - ys) / 300.0, 0, 1)
    m = (np.minimum(up, down) ** 1.25)[:, None, None] * strength
    return np.clip(out * (1 - m), 0, 255).astype(np.uint8)


def glow(radius, color, strength=90):
    """Resplandor radial para el emblema del cierre."""
    size = radius * 2
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    dist = np.sqrt((xx - radius) ** 2 + (yy - radius) ** 2) / radius
    a = np.clip(1 - dist, 0, 1) ** 2.4 * strength
    img = np.zeros((size, size, 4), np.uint8)
    img[..., 0], img[..., 1], img[..., 2] = color
    img[..., 3] = a.astype(np.uint8)
    return img


def load_rgba(path, size=None):
    im = Image.open(path).convert("RGBA")
    if size:
        im = im.resize(size, Image.Resampling.LANCZOS)
    return np.array(im)


# ---------------------------------------------------------------- cámara virtual
class Camera:
    """Mueve una ventana de recorte sobre la placa 1296x2304 y la entrega a 1080x1920."""

    def __init__(self, z=(1.0, 1.0), c=((0.5, 0.5), (0.5, 0.5)), ease="out",
                 rot=(0.0, 0.0), shake=0.0, shake_hz=(7.3, 11.1), seed=0):
        self.z0, self.z1 = z
        self.c0, self.c1 = c
        self.ease = EASES[ease]
        self.rot0, self.rot1 = rot
        self.shake = shake
        self.hz = shake_hz
        self.seed = seed

    def state(self, p):
        e = self.ease(p)
        z = self.z0 + (self.z1 - self.z0) * e
        cx = (self.c0[0] + (self.c1[0] - self.c0[0]) * e) * OVW
        cy = (self.c0[1] + (self.c1[1] - self.c0[1]) * e) * OVH
        rot = self.rot0 + (self.rot1 - self.rot0) * e
        if self.shake:
            t = p * 3.0
            cx += math.sin(t * self.hz[0] + self.seed) * self.shake * 9
            cy += math.cos(t * self.hz[1] + self.seed * 2) * self.shake * 7
            rot += math.sin(t * 5.1 + self.seed) * self.shake * 0.35
        return z, cx, cy, rot


def crop_window(frame, z, cx, cy, rot=0.0):
    """Recorta la ventana de la cámara (sin remuestrear dos veces) y la escala al encuadre final."""
    w = OVW / z
    h = OVH / z
    x0 = cx - w / 2
    y0 = cy - h / 2
    # clamp dentro de la placa
    x0 = min(max(x0, 0), OVW - w)
    y0 = min(max(y0, 0), OVH - h)
    xi, yi = int(round(x0)), int(round(y0))
    wi, hi = int(round(w)), int(round(h))
    crop = frame[yi:yi + hi, xi:xi + wi]
    if abs(rot) > 0.01:
        m = cv2.getRotationMatrix2D((wi / 2, hi / 2), rot, 1.0)
        crop = cv2.warpAffine(crop, m, (wi, hi), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    interp = cv2.INTER_AREA if wi > W else cv2.INTER_LANCZOS4
    return cv2.resize(crop, (W, H), interpolation=interp)


# ---------------------------------------------------------------- efectos
def motion_blur(img, strength, angle_deg):
    if strength <= 0.4:
        return img
    taps = 7
    acc = np.zeros_like(img, np.float32)
    a = math.radians(angle_deg)
    dx, dy = math.cos(a), math.sin(a)
    for i in range(taps):
        t = (i / (taps - 1) - 0.5) * 2
        m = np.float32([[1, 0, dx * t * strength], [0, 1, dy * t * strength]])
        acc += cv2.warpAffine(img, m, (img.shape[1], img.shape[0]), flags=cv2.INTER_LINEAR,
                              borderMode=cv2.BORDER_REPLICATE).astype(np.float32)
    return (acc / taps).astype(np.uint8)


def radial_blur(img, strength):
    if strength <= 0.4:
        return img
    h, w = img.shape[:2]
    acc = np.zeros_like(img, np.float32)
    for i, s in enumerate((1.0, 1.02, 0.98, 1.045, 0.955)):
        m = cv2.getRotationMatrix2D((w / 2, h / 2), 0, s)
        acc += cv2.warpAffine(img, m, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE).astype(np.float32)
    blend = acc / 5
    return (img.astype(np.float32) * (1 - strength) + blend * strength).astype(np.uint8)


def paste_rgba(dst, src, x=None, y=None, alpha=1.0, center=False):
    if alpha <= 0.004:
        return
    h, w = src.shape[:2]
    if center or x is None:
        x = (dst.shape[1] - w) // 2
    if center or y is None:
        y = (dst.shape[0] - h) // 2
    x, y = int(round(x)), int(round(y))
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(dst.shape[1], x + w), min(dst.shape[0], y + h)
    if x1 <= x0 or y1 <= y0:
        return
    sub = src[y0 - y:y1 - y, x0 - x:x1 - x]
    a = (sub[..., 3:4].astype(np.float32) / 255.0) * alpha
    region = dst[y0:y1, x0:x1].astype(np.float32)
    dst[y0:y1, x0:x1] = np.clip(region * (1 - a) + sub[..., :3].astype(np.float32) * a, 0, 255).astype(np.uint8)


def make_vignette(strength=0.42, power=2.1):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    nx = (xx - W / 2) / (W / 2)
    ny = (yy - H / 2) / (H / 2)
    r = np.sqrt(nx ** 2 * 0.85 + ny ** 2)
    v = 1.0 - np.clip(r, 0, 1.6) ** power * strength
    return np.clip(v, 0, 1)[..., None].astype(np.float32)


def make_grain_tiles(n=8, amount=6.0):
    rng = np.random.default_rng(7)
    tiles = []
    for _ in range(n):
        t = rng.normal(0, amount, (H, W, 1)).astype(np.float32)
        t = cv2.GaussianBlur(t, (0, 0), 0.7)[..., None] if False else t
        tiles.append(t)
    return tiles


def finish(img, vignette, grain_tile, grain_amount=1.0, warmth=0.0, contrast=1.0):
    out = img.astype(np.float32)
    if contrast != 1.0:
        out = (out - 128.0) * contrast + 128.0
    if warmth:
        out[..., 0] += warmth * 3.0
        out[..., 2] -= warmth * 2.4
    if vignette.ndim == 2:
        vignette = vignette[..., None]
    if grain_tile.ndim == 2:
        grain_tile = grain_tile[..., None]
    out = out * vignette
    out += grain_tile * grain_amount
    return np.clip(out, 0, 255).astype(np.uint8)


def flash_frame(img, amount):
    if amount <= 0:
        return img
    a = np.clip(amount, 0, 1)
    return np.clip(img.astype(np.float32) * (1 - a) + np.array(PAPER, np.float32) * a, 0, 255).astype(np.uint8)


def darken_blur(img, factor=0.45, blur=7):
    out = cv2.GaussianBlur(img, (0, 0), blur)
    return np.clip(out.astype(np.float32) * factor, 0, 255).astype(np.uint8)
