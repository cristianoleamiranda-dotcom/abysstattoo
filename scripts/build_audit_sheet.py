#!/usr/bin/env python3
"""
build_audit_sheet.py — Genera la lámina de Auditoría y Curaduría Previa (Antes vs. Después)
demostrando el filtrado, recorte, corrección de numeración oficial (528) y tone-mapping HDR->BT.709.
"""

import os
import shutil
import subprocess

import cv2
from PIL import Image, ImageDraw, ImageFont

ROOT = "/home/user/abysstattoo"
os.chdir(ROOT)


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
STORY = "dropbox/story_ubicacion_aerea_abyss_1080p.mp4"
OUT = "film/auditoria_edicion_material_reel.jpg"

OBSIDIAN = (18, 14, 12)
PANEL = (26, 21, 18)
CARD = (32, 26, 22)
BONE = (181, 162, 149)
CREAM = (234, 227, 221)
PAPER = (246, 241, 237)
TEAL_L = (158, 196, 186)
SAGE = (85, 108, 101)
WARN = (214, 132, 114)

F = lambda p, s: ImageFont.truetype(p, s)
cin800 = F("assets/fonts/cinzel-800.ttf", 36)
m700 = F("assets/fonts/montserrat-700.ttf", 17)
m600 = F("assets/fonts/montserrat-600.ttf", 15)
m500 = F("assets/fonts/montserrat-500.ttf", 14)


def grab_video(path: str, t: float) -> Image.Image:
    cap = cv2.VideoCapture(path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(round(t * fps)))
    ok, fr = cap.read()
    cap.release()
    if not ok:
        raise RuntimeError(f"No se pudo leer {path} en t={t}")
    return Image.fromarray(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB))


def fit_cover(im: Image.Image, tw: int, th: int) -> Image.Image:
    w, h = im.size
    r = tw / th
    if w / h > r:
        nw = int(round(h * r))
        x0 = (w - nw) // 2
        im = im.crop((x0, 0, x0 + nw, h))
    else:
        nh = int(round(w / r))
        y0 = (h - nh) // 2
        im = im.crop((0, y0, w, y0 + nh))
    return im.resize((tw, th), Image.Resampling.LANCZOS)


def draw_wrapped(draw: ImageDraw.ImageDraw, text: str, x: int, y: int, max_w: int, fnt, fill, line_h: int = 20):
    words = text.split()
    line, lines = "", []
    for w in words:
        probe = (line + " " + w).strip()
        if draw.textlength(probe, font=fnt) > max_w and line:
            lines.append(line)
            line = w
        else:
            line = probe
    if line:
        lines.append(line)
    for ln in lines[:4]:
        draw.text((x, y), ln, font=fnt, fill=fill)
        y += line_h
    return y


def main():
    raw_drone = grab_video(STORY, 1.05)
    cur_drone = grab_video("assets/reel_plates/plate_v03_dron_aereo.mp4", 1.05)

    raw_hall = grab_video(STORY, 7.60)
    cur_hall = grab_video("assets/reel_plates/plate_v04_pasillo_pov.mp4", 0.50)

    raw_promo = grab_video(STORY, 13.00)
    cur_facade = Image.open("assets/reel_plates/plate_p01_fachada_real.jpg").convert("RGB")

    raw_hdr = grab_video("film/proceso_detalle.mp4", 7.10)
    cur_hdr = grab_video("assets/reel_plates/plate_v06_wipe_reveal.mp4", 1.08)

    cases = [
        (
            "01 · VUELO AÉREO FPV SAN BERNARDO",
            raw_drone,
            cur_drone,
            "CRUDO: rótulo quemado superior + dirección errónea '548' abajo.",
            "EDITADO: recorte óptico 9:16 + dirección corregida 'J. J. Pérez 528'.",
            raw_drone.crop((320, 1465, 760, 1845)),
        ),
        (
            "02 · TRAVELLING POV INTERIOR",
            raw_hall,
            cur_hall,
            "CRUDO: cabecera 'RECORRIDO DEL ESTUDIO' y barra inferior quemadas.",
            "EDITADO: cámara subjetiva limpia + overscan 20 % + curva LAB.",
            cur_hall.crop((180, 780, 1116, 1520)),
        ),
        (
            "03 · DESCARTE DE PROMOS FLASH",
            raw_promo,
            cur_facade,
            "DESCARTADO: '20% / 10% / $70.000 / 548' y letrero IA deformado.",
            "SELECCIONADO: fachada real verificada en José Joaquín Pérez 528.",
            cur_facade.crop((140, 420, 1156, 1180)),
        ),
        (
            "04 · TONE-MAPPING HDR -> BT.709",
            raw_hdr,
            cur_hdr,
            "CRUDO: video 10-bit HLG (BT.2020) con piel sobreexpuesta naranja.",
            "EDITADO: compresión soft-knee BT.709 + Ink Wipe Reveal natural.",
            cur_hdr.crop((140, 620, 1156, 1420)),
        ),
    ]

    W, H = 2080, 1240
    sheet = Image.new("RGB", (W, H), OBSIDIAN)
    d = ImageDraw.Draw(sheet)

    pad = 34
    d.text((pad, 30), "AUDITORÍA, SELECCIÓN Y EDICIÓN PREVIA — REEL COMERCIAL ABYSS (528)", font=cin800, fill=PAPER)
    d.text(
        (pad, 80),
        "Inspección técnica previa al montaje: descarte de campañas obsoletas y UI móvil, corrección de numeración oficial (José Joaquín Pérez 528) y etalonaje BT.709.",
        font=m500,
        fill=BONE,
    )
    d.line([(pad, 116), (W - pad, 116)], fill=SAGE, width=2)

    col_gap = 24
    col_w = (W - pad * 2 - col_gap * 3) // 4
    card_y0, card_y1 = 140, H - 34

    for idx, (title, im_raw, im_cur, txt_raw, txt_cur, zoom_crop) in enumerate(cases):
        cx = pad + idx * (col_w + col_gap)
        d.rounded_rectangle((cx, card_y0, cx + col_w, card_y1), radius=12, fill=PANEL, outline=(62, 52, 45), width=1)
        d.text((cx + 18, card_y0 + 16), title, font=m700, fill=TEAL_L)

        # Par comparativo Antes / Después (cada columna tiene su propio ancho estricto sin colisión)
        inner_pad = 16
        pair_gap = 12
        pw = (col_w - inner_pad * 2 - pair_gap) // 2
        ph = int(pw * 16 / 9)
        py = card_y0 + 54

        p_raw = fit_cover(im_raw, pw, ph)
        p_cur = fit_cover(im_cur, pw, ph)
        lx = cx + inner_pad
        rx = lx + pw + pair_gap

        sheet.paste(p_raw, (lx, py))
        d.rectangle((lx, py, lx + pw, py + ph), outline=WARN, width=2)
        sheet.paste(p_cur, (rx, py))
        d.rectangle((rx, py, rx + pw, py + ph), outline=TEAL_L, width=2)

        ty = py + ph + 12
        d.text((lx, ty), "ORIGINAL / CRUDO", font=m700, fill=WARN)
        d.text((rx, ty), "CURADO / MASTER", font=m700, fill=TEAL_L)

        y_after_l = draw_wrapped(d, txt_raw, lx, ty + 24, pw - 4, m500, (186, 174, 165), 19)
        y_after_r = draw_wrapped(d, txt_cur, rx, ty + 24, pw - 4, m500, CREAM, 19)

        zy = max(y_after_l, y_after_r) + 16
        zh = card_y1 - zy - 16
        zw = col_w - inner_pad * 2
        if zh > 80:
            z_im = fit_cover(zoom_crop, zw, zh)
            sheet.paste(z_im, (lx, zy))
            d.rectangle((lx, zy, lx + zw, zy + zh), outline=(74, 63, 55), width=1)

    sheet.save(OUT, quality=92)
    print(f"Auditoría guardada: {OUT} ({sheet.size})")


if __name__ == "__main__":
    main()
