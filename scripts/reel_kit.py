#!/usr/bin/env python3
"""
reel_kit.py — Kit de dirección óptica, cámara virtual 3D sub-píxel, tipografía cinética y postproducción.
Módulos activos: PhotoCraft + LightCraft + VectorCraft + FilmCraft (Abyss Tattoo Studio · 528).
"""

import math

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------- paleta oficial Abyss
OBSIDIAN = (20, 16, 13)      # #14100D
PANEL = (26, 21, 18)         # #1A1512
BONE = (181, 162, 149)       # #B5A295
BONE_L = (198, 183, 171)     # #C6B7AB
CREAM = (234, 227, 221)      # #EAE3DD
PAPER = (246, 241, 237)      # #F6F1ED
SAGE = (85, 108, 101)        # #556C65
TEAL = (108, 146, 138)       # #6C928A
TEAL_L = (158, 196, 186)     # #9EC4BA

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
    "mont400": "assets/fonts/montserrat-400.ttf",
}
_font_cache = {}


def font(key: str, size: int) -> ImageFont.FreeTypeFont:
    k = (key, size)
    if k not in _font_cache:
        _font_cache[k] = ImageFont.truetype(FONTS[key], size)
    return _font_cache[k]


# ---------------------------------------------------------------- curvas físicas de easing
def clamp01(x: float) -> float:
    return 0.0 if x < 0.0 else (1.0 if x > 1.0 else x)


def ease_out_quart(p: float) -> float:
    p = clamp01(p)
    return 1.0 - (1.0 - p) ** 4


def ease_out_quint(p: float) -> float:
    p = clamp01(p)
    return 1.0 - (1.0 - p) ** 5


def ease_out_cubic(p: float) -> float:
    p = clamp01(p)
    return 1.0 - (1.0 - p) ** 3


def ease_in_cubic(p: float) -> float:
    p = clamp01(p)
    return p ** 3


def ease_in_out_cubic(p: float) -> float:
    p = clamp01(p)
    return 4.0 * p ** 3 if p < 0.5 else 1.0 - (-2.0 * p + 2.0) ** 3 / 2.0


def ease_speed_ramp(p: float) -> float:
    """Arranque rápido de impacto, planeo óptico suave en medio y aceleración al corte de salida."""
    p = clamp01(p)
    if p < 0.28:
        q = p / 0.28
        return 0.42 * (1.0 - (1.0 - q) ** 3)
    if p < 0.78:
        q = (p - 0.28) / 0.50
        return 0.42 + 0.30 * q
    q = (p - 0.78) / 0.22
    return 0.72 + 0.28 * (q ** 2.4)


def ease_out_back(p: float, s: float = 1.28) -> float:
    p = clamp01(p)
    return 1.0 + (s + 1.0) * (p - 1.0) ** 3 + s * (p - 1.0) ** 2


EASES = {
    "linear": clamp01,
    "out": ease_out_quart,
    "out5": ease_out_quint,
    "outcubic": ease_out_cubic,
    "in": ease_in_cubic,
    "inout": ease_in_out_cubic,
    "ramp": ease_speed_ramp,
    "back": ease_out_back,
}


# ---------------------------------------------------------------- tipografía editorial precisa
def measure_tracked(text: str, fnt: ImageFont.FreeTypeFont, tracking: float = 0.0):
    """Mide el ancho real con kerning/tracking y la caja de tinta exacta (ink bbox)."""
    adv = sum(fnt.getlength(ch) + tracking for ch in text) - (tracking if text else 0)
    # Caja vertical real de mayúsculas/ascendentes para centrado óptico exacto
    ref_bbox = fnt.getbbox(text or "Ag")
    ink_top, ink_bot = ref_bbox[1], ref_bbox[3]
    ink_h = max(1, ink_bot - ink_top)
    return float(max(1.0, adv)), ink_top, ink_bot, ink_h


def tracked_text(
    text: str,
    fnt: ImageFont.FreeTypeFont,
    fill: tuple,
    tracking: float = 0.0,
    pad: int = 8,
    shadow: bool = False,
) -> np.ndarray:
    """Renderiza texto con tracking preciso usando el ink-bbox real (cero desalineación vertical)."""
    tw, ink_top, ink_bot, ink_h = measure_tracked(text, fnt, tracking)
    img_w = int(math.ceil(tw)) + pad * 2
    img_h = ink_h + pad * 2
    img = Image.new("RGBA", (img_w, img_h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    y_draw = pad - ink_top
    if shadow:
        x = float(pad) + 2.0
        for ch in text:
            d.text((x, y_draw + 3), ch, font=fnt, fill=(8, 6, 5, 165))
            x += fnt.getlength(ch) + tracking
    x = float(pad)
    for ch in text:
        d.text((x, y_draw), ch, font=fnt, fill=fill + (255,))
        x += fnt.getlength(ch) + tracking
    return np.array(img)


def stack(items, top: float, display_gap: float = 0.14, block_gap: float = 0.44, align: str = "center", x_anchor: float = 540.0):
    """Apila líneas tipográficas respetando sus cajas reales sin solaparse jamás."""
    y = float(top)
    out = []
    prev_kind = None
    for it in items:
        text, fkey, size, color, tracking, t0, style = it[:7]
        kind = it[7] if len(it) > 7 else "line"
        shadow = it[8] if len(it) > 8 else True
        img = tracked_text(text, font(fkey, size), color, tracking, shadow=shadow)
        if prev_kind == "display" and kind == "display":
            y += size * display_gap
        elif prev_kind is not None:
            y += size * block_gap
        if align == "left":
            cx = x_anchor + img.shape[1] / 2.0
        elif align == "right":
            cx = x_anchor - img.shape[1] / 2.0
        else:
            cx = x_anchor
        out.append((img, cx, y + img.shape[0] / 2.0, t0, style))
        y += img.shape[0]
        prev_kind = kind
    return out


def diamond(draw: ImageDraw.ImageDraw, cx: float, cy: float, r: float, fill: tuple, alpha: int = 255):
    draw.polygon([(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)], fill=fill + (alpha,))


def line_alpha(draw: ImageDraw.ImageDraw, pts, fill: tuple, width: int = 2, alpha: int = 255):
    draw.line(pts, fill=fill + (alpha,), width=width)


def pill(
    text: str,
    fnt_key: str,
    size: int,
    tracking: float,
    fg: tuple,
    bg: tuple,
    border: tuple = None,
    pad_x: int = 44,
    pad_y: int = 24,
    with_diamond: bool = True,
    diamond_color: tuple = None,
) -> np.ndarray:
    """Pastilla CTA con centrado óptico vertical exacto al medio píxel y rombos simétricos."""
    fnt = font(fnt_key, size)
    tw, ink_top, ink_bot, ink_h = measure_tracked(text, fnt, tracking)
    diam_r = max(6, int(round(size * 0.24)))
    gap = int(round(size * 0.52))
    side_extra = (diam_r * 2 + gap) if with_diamond else 0

    content_w = tw + (side_extra * 2 if with_diamond else 0)
    w = int(math.ceil(content_w)) + pad_x * 2
    h = ink_h + pad_y * 2

    # Supersampling 2x para bordes curvos y diamantes perfectamente antialiasing
    ss = 2
    img_hi = Image.new("RGBA", (w * ss, h * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(img_hi)

    # Cuerpo principal + filete interior sutil
    d.rounded_rectangle(
        (2, 2, w * ss - 3, h * ss - 3),
        radius=(h * ss) // 2,
        fill=bg + (255,),
        outline=(border + (235,)) if border else (BONE + (180,)),
        width=2 * ss,
    )

    fnt_hi = font(fnt_key, size * ss)
    tw_hi, ink_top_hi, _, ink_h_hi = measure_tracked(text, fnt_hi, tracking * ss)
    cy_hi = (h * ss) / 2.0
    y_text_hi = cy_hi - ink_h_hi / 2.0 - ink_top_hi

    total_inner_hi = tw_hi + (2 * (diam_r * 2 + gap) * ss if with_diamond else 0)
    cursor_x = (w * ss - total_inner_hi) / 2.0

    if with_diamond:
        dc = diamond_color or fg
        diamond(d, cursor_x + diam_r * ss, cy_hi, diam_r * ss, dc, 255)
        cursor_x += (diam_r * 2 + gap) * ss

    for ch in text:
        d.text((cursor_x, y_text_hi), ch, font=fnt_hi, fill=fg + (255,))
        cursor_x += fnt_hi.getlength(ch) + tracking * ss

    if with_diamond:
        cursor_x += gap * ss - tracking * ss
        dc = diamond_color or fg
        diamond(d, cursor_x + diam_r * ss, cy_hi, diam_r * ss, dc, 255)

    return np.array(img_hi.resize((w, h), Image.Resampling.LANCZOS))


def callout_badge(tag: str, label: str, accent: tuple = TEAL_L) -> np.ndarray:
    """Etiqueta técnica estilo Solen HUD: •───╲  TAG · LABEL."""
    f1 = font("mont700", 19)
    f2 = font("mont500", 19)
    w1, t1, _, h1 = measure_tracked(tag, f1, 4)
    w2, t2, _, h2 = measure_tracked(label, f2, 3)
    w = int(76 + w1 + 26 + w2 + 28)
    h = 44
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((46, 2, w - 2, h - 2), radius=6, fill=(16, 13, 11, 188), outline=BONE + (92,), width=1)
    # Punto + línea quebrada de llamada
    d.ellipse((2, h // 2 - 4, 10, h // 2 + 4), fill=accent + (255,))
    d.line([(10, h // 2), (34, h // 2), (46, h // 2)], fill=accent + (215,), width=2)
    cy = h / 2.0
    x = 62.0
    for ch in tag:
        d.text((x, cy - h1 / 2.0 - t1), ch, font=f1, fill=accent + (255,))
        x += f1.getlength(ch) + 4
    d.polygon([(x + 6, cy - 4), (x + 10, cy), (x + 6, cy + 4), (x + 2, cy)], fill=BONE + (210,))
    x += 20.0
    for ch in label:
        d.text((x, cy - h2 / 2.0 - t2), ch, font=f2, fill=CREAM + (245,))
        x += f2.getlength(ch) + 3
    return np.array(im)


def corner_hud(alpha: int = 138, inset=(64, 198, 1016, 1510), length: int = 46, color=BONE, width: int = 2) -> np.ndarray:
    """Escuadras ópticas ┌ ┐ └ ┘ dentro de la zona segura de Instagram Reels."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    x0, y0, x1, y1 = inset
    for (cx, cy, sx, sy) in [(x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)]:
        line_alpha(d, [(cx, cy), (cx + sx * length, cy)], color, width, alpha)
        line_alpha(d, [(cx, cy), (cx, cy + sy * length)], color, width, alpha)
    return np.array(img)


def divider(width: int, color_line: tuple, color_dot: tuple, alpha: int = 220, r: int = 9) -> np.ndarray:
    h = 28
    img = Image.new("RGBA", (width, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cy = h // 2
    gap = r * 3
    d.line([(0, cy), (width // 2 - gap, cy)], fill=color_line + (alpha,), width=2)
    d.line([(width // 2 + gap, cy), (width, cy)], fill=color_line + (alpha,), width=2)
    diamond(d, width // 2, cy, r, color_dot, alpha)
    return np.array(img)


def concentric_rings(size: int = 760, rings: int = 8, color: tuple = BONE, max_alpha: int = 34) -> np.ndarray:
    """Anillos concéntricos grabados sutiles inspirados en el sello oficial de Abyss."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c = size // 2
    for i in range(rings):
        r = int(size * (0.20 + 0.29 * (i / max(1, rings - 1))))
        a = int(max_alpha * (1.0 - i / (rings + 1.5)))
        d.ellipse((c - r, c - r, c + r, c + r), outline=color + (a,), width=1)
    return np.array(img)


def glow(radius: int, color: tuple, strength: float = 85.0) -> np.ndarray:
    size = radius * 2
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    dist = np.sqrt((xx - radius) ** 2 + (yy - radius) ** 2) / radius
    a = np.clip(1.0 - dist, 0.0, 1.0) ** 2.3 * strength
    img = np.zeros((size, size, 4), np.uint8)
    img[..., 0], img[..., 1], img[..., 2] = color
    img[..., 3] = a.astype(np.uint8)
    return img


def load_rgba(path: str, size=None) -> np.ndarray:
    im = Image.open(path).convert("RGBA")
    if size:
        im = im.resize(size, Image.Resampling.LANCZOS)
    return np.array(im)


# ---------------------------------------------------------------- RIG DE CÁMARA VIRTUAL 3D SUB-PÍXEL
class Camera:
    """
    Rig cinematográfico 3D sub-píxel sobre placa overscan 1296x2304 -> salida 1080x1920.
    Soporta:
      - Zoom óptico continuo (push-in, pull-out, crash zoom, speed-ramp)
      - Travelling X/Y sub-píxel (paneo lateral, tilt ascendente/descendente)
      - Rotación Dutch Roll (rot en grados)
      - Inclinación de perspectiva 3D real (pitch_y, yaw_x) para tiros arquitectónicos
      - Respiración orgánica de cámara en mano (handheld micro-float)
    """

    def __init__(
        self,
        z=(1.04, 1.18),
        c=((0.50, 0.50), (0.50, 0.50)),
        ease="out",
        rot=(0.0, 0.0),
        tilt=((0.0, 0.0), (0.0, 0.0)),
        shake=0.0,
        shake_hz=(6.7, 9.9),
        seed=0,
    ):
        self.z0, self.z1 = z
        self.c0, self.c1 = c
        self.ease = EASES[ease]
        self.rot0, self.rot1 = rot
        self.t0, self.t1 = tilt
        self.shake = shake
        self.hz = shake_hz
        self.seed = seed

    def state(self, p: float):
        e = self.ease(p)
        z = self.z0 + (self.z1 - self.z0) * e
        cx = (self.c0[0] + (self.c1[0] - self.c0[0]) * e) * OVW
        cy = (self.c0[1] + (self.c1[1] - self.c0[1]) * e) * OVH
        rot = self.rot0 + (self.rot1 - self.rot0) * e
        tx = self.t0[0] + (self.t1[0] - self.t0[0]) * e
        ty = self.t0[1] + (self.t1[1] - self.t0[1]) * e
        if self.shake > 0:
            t = p * 3.2
            cx += math.sin(t * self.hz[0] + self.seed) * self.shake * 8.5
            cy += math.cos(t * self.hz[1] + self.seed * 1.9) * self.shake * 6.5
            rot += math.sin(t * 4.7 + self.seed) * self.shake * 0.32
        return z, cx, cy, rot, tx, ty


def render_camera(frame: np.ndarray, z: float, cx: float, cy: float, rot: float = 0.0, tx: float = 0.0, ty: float = 0.0, out_w: int = W, out_h: int = H) -> np.ndarray:
    """
    Transformación proyectiva 3x3 de una sola pasada en coma flotante:
    cero saltos de píxel entero a 60 fps + inclinación 3D opcional.
    """
    fh, fw = frame.shape[:2]
    # Escala base para cubrir out_w x out_h con factor de zoom z (relativo al overscan 1296x2304)
    base_scale = (out_w / float(W)) * (float(W) / float(fw)) * float(OVW / W) * z
    # Ajuste exacto: cuando frame es 1296x2304 y out es 1080x1920, z=1.0 mapea ventana 1296x2304 -> 1080x1920;
    # z=1.20 mapea 1080x1920 1:1 al píxel nativo.
    s = (out_w / float(fw)) * z
    rad = math.radians(rot)
    cos_a, sin_a = math.cos(rad) * s, math.sin(rad) * s

    # Matriz de traslación al centro (cx, cy) + rotación + escala -> centro (out_w/2, out_h/2)
    T1 = np.array([[1.0, 0.0, -cx], [0.0, 1.0, -cy], [0.0, 0.0, 1.0]], dtype=np.float64)
    R = np.array([[cos_a, -sin_a, 0.0], [sin_a, cos_a, 0.0], [0.0, 0.0, 1.0]], dtype=np.float64)
    # Perspectiva 3D sutil (yaw tx, pitch ty) centrada en el eje óptico
    P = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [tx * 1e-4, ty * 1e-4, 1.0]], dtype=np.float64)
    T2 = np.array([[1.0, 0.0, out_w / 2.0], [0.0, 1.0, out_h / 2.0], [0.0, 0.0, 1.0]], dtype=np.float64)
    H_mat = T2 @ P @ R @ T1

    return cv2.warpPerspective(
        frame,
        H_mat,
        (out_w, out_h),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_REFLECT_101,
    )


# ---------------------------------------------------------------- efectos ópticos rápidos
def motion_blur(img: np.ndarray, strength: float, angle_deg: float) -> np.ndarray:
    """Desenfoque direccional de obturador rápido mediante kernel lineal convolucional OpenCV C++."""
    if strength <= 0.7:
        return img
    ksize = max(3, min(45, int(round(strength * 1.35)) | 1))
    kernel = np.zeros((ksize, ksize), dtype=np.float32)
    c = ksize // 2
    rad = math.radians(angle_deg)
    dx, dy = math.cos(rad), math.sin(rad)
    steps = ksize * 2
    for i in range(steps):
        t = (i / (steps - 1) - 0.5) * (ksize - 1)
        x = int(round(c + dx * t))
        y = int(round(c + dy * t))
        if 0 <= x < ksize and 0 <= y < ksize:
            kernel[y, x] += 1.0
    kernel /= max(kernel.sum(), 1e-6)
    return cv2.filter2D(img, -1, kernel, borderType=cv2.BORDER_REPLICATE)


def radial_zoom_blur(img: np.ndarray, amount: float) -> np.ndarray:
    """Desenfoque radial de hiper-zoom para entradas de impacto y picada de dron."""
    if amount <= 0.02:
        return img
    h, w = img.shape[:2]
    m1 = cv2.getRotationMatrix2D((w / 2.0, h / 2.0), 0.0, 1.032)
    m2 = cv2.getRotationMatrix2D((w / 2.0, h / 2.0), 0.0, 0.970)
    z1 = cv2.warpAffine(img, m1, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    z2 = cv2.warpAffine(img, m2, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    mid = cv2.addWeighted(z1, 0.5, z2, 0.5, 0)
    return cv2.addWeighted(img, 1.0 - amount, mid, amount, 0)


def paste_rgba(dst: np.ndarray, src: np.ndarray, x=None, y=None, alpha: float = 1.0, center: bool = False):
    """Composición alfa ultrarrápida en aritmética entera uint16."""
    if alpha <= 0.004:
        return
    h, w = src.shape[:2]
    if x is None:
        x = (dst.shape[1] - w) // 2
    if y is None:
        y = (dst.shape[0] - h) // 2
    x, y = int(round(x)), int(round(y))
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(dst.shape[1], x + w), min(dst.shape[0], y + h)
    if x1 <= x0 or y1 <= y0:
        return
    sub = src[y0 - y : y1 - y, x0 - x : x1 - x]
    a16 = ((sub[..., 3:4].astype(np.uint16) * int(round(clamp01(alpha) * 256))) >> 8)
    inv16 = 256 - a16
    reg = dst[y0:y1, x0:x1].astype(np.uint16)
    dst[y0:y1, x0:x1] = ((reg * inv16 + sub[..., :3].astype(np.uint16) * a16) >> 8).astype(np.uint8)


def paste_rgba_shimmer(dst: np.ndarray, src: np.ndarray, cx: float, cy: float, alpha: float = 1.0, shimmer_p: float = -1.0):
    """Dibuja un botón CTA con barrido especular diagonal de lujo cuando shimmer_p ∈ [0, 1]."""
    img = src
    if 0.0 <= shimmer_p <= 1.0:
        img = src.copy()
        h, w = img.shape[:2]
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        diag = (xx + yy * 0.45) / (w + h * 0.45)
        band = np.exp(-((diag - shimmer_p) ** 2) / (2.0 * 0.0045))
        boost = (band * 58.0)[..., None]
        img[..., :3] = np.clip(img[..., :3].astype(np.float32) + boost, 0, 255).astype(np.uint8)
    paste_rgba(dst, img, cx - img.shape[1] / 2.0, cy - img.shape[0] / 2.0, alpha)


def make_scrim_lut(mode: str) -> np.ndarray:
    """Precalcula máscara multiplicativa uint16 (0..256) por fila para contraste editorial instantáneo."""
    ys = np.linspace(0.0, 1.0, H, dtype=np.float32)
    if mode == "lower":
        # Deja libre y nítido el 60 % superior (arte/rostro/dron) y oscurece suavemente el tercio inferior
        top_shield = 1.0 - 0.30 * np.exp(-((ys - 0.08) ** 2) / 0.012)
        bot_ramp = 1.0 - 0.74 * (np.clip((ys - 0.50) / 0.42, 0.0, 1.0) ** 1.45)
        mult = top_shield * bot_ramp
    elif mode == "hero_center":
        # Para el Hook de impacto (0-2.4s): contraste central cinematográfico sin apagar bordes
        center_dip = 1.0 - 0.52 * np.exp(-((ys - 0.56) ** 2) / 0.045)
        edges = 1.0 - 0.36 * (np.abs(ys - 0.5) * 2.0) ** 2.6
        mult = center_dip * edges
    elif mode == "split":
        # Banda central limpia en Obsidiana alrededor de y=960 para el Split-Screen de Piercing
        center_band = 1.0 - 0.88 * np.exp(-((ys - 0.50) ** 2) / 0.0085)
        edges = 1.0 - 0.30 * (np.abs(ys - 0.5) * 2.0) ** 3.0
        mult = center_band * edges
    else:
        mult = np.ones_like(ys)
    return np.clip(mult * 256.0, 0, 256).astype(np.uint16)[:, None, None]


def apply_scrim_fast(img: np.ndarray, lut_col: np.ndarray) -> np.ndarray:
    return ((img.astype(np.uint16) * lut_col) >> 8).astype(np.uint8)


def make_vignette_u16(strength: float = 0.38, power: float = 2.2) -> np.ndarray:
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    nx = (xx - W / 2.0) / (W / 2.0)
    ny = (yy - H / 2.0) / (H / 2.0)
    r = np.sqrt(nx ** 2 * 0.85 + ny ** 2)
    v = 1.0 - np.clip(r, 0.0, 1.6) ** power * strength
    return np.clip(v * 256.0, 0, 256).astype(np.uint16)[..., None]


def make_grain_tiles_i16(n: int = 8, amount: float = 4.6):
    rng = np.random.default_rng(7)
    return [rng.normal(0.0, amount, (H, W, 1)).astype(np.int16) for _ in range(n)]


def finish_fast(img: np.ndarray, vignette_u16: np.ndarray, grain_i16: np.ndarray) -> np.ndarray:
    """Acabado cinematográfico final (viñeta óptica + grano de película 35mm) en ~2 ms/frame."""
    v = ((img.astype(np.uint16) * vignette_u16) >> 8).astype(np.int16)
    return np.clip(v + grain_i16, 0, 255).astype(np.uint8)


def flash_frame(img: np.ndarray, amount: float, tint=PAPER) -> np.ndarray:
    if amount <= 0.005:
        return img
    a = int(round(clamp01(amount) * 256))
    inv = 256 - a
    t = np.array(tint, dtype=np.uint16)[None, None, :]
    return ((img.astype(np.uint16) * inv + t * a) >> 8).astype(np.uint8)
