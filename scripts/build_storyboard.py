#!/usr/bin/env python3
"""Genera el guion gráfico (storyboard) del reel comercial a partir del máster renderizado."""

import os
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = "/home/user/abysstattoo"
os.chdir(ROOT)
FFMPEG = f"{ROOT}/.venv/bin/ffmpeg"
MASTER = "film/reel_comercial_abyss_15s_1080x1920_60fps_master.mp4"
OUT = "film/storyboard_reel_abyss_15s.jpg"

OBSIDIAN, PANEL, BONE, CREAM, PAPER, TEAL_L, SAGE = (
    (18, 14, 12), (26, 21, 18), (181, 162, 149), (234, 227, 221), (246, 241, 237), (158, 196, 186), (85, 108, 101))

F = lambda p, s: ImageFont.truetype(p, s)
cin800 = F("assets/fonts/cinzel-800.ttf", 40)
cin600 = F("assets/fonts/cinzel-600.ttf", 30)
m700 = F("assets/fonts/montserrat-700.ttf", 19)
m600 = F("assets/fonts/montserrat-600.ttf", 18)
m500 = F("assets/fonts/montserrat-500.ttf", 17)
m400 = F("assets/fonts/montserrat-400.ttf", 16)

SHOTS = [
    (0.75, "01", "0,00 – 1,20 s", "ECU · MACRO", "85 mm · push-in c/ shake", "ESTO NO ES / UN TATUAJE.", "Hook de textura: la aguja entra antes que cualquier logo."),
    (1.95, "02", "1,20 – 2,40 s", "PRIMER PLANO", "50 mm · push-in", "ES UNA FIRMA. / REALISMO BLACK & GREY", "Pago del hook: la promesa se cumple con la obra en cuadro."),
    (3.30, "03", "2,40 – 4,20 s", "PLANO GENERAL", "24 mm · travelling ascendente", "SAN BERNARDO · DESDE 2009", "Establece ubicación y trayectoria: el estudio existe y tiene historia."),
    (4.80, "04", "4,20 – 5,40 s", "TRAVELLING", "35 mm · dolly-in", "ENTRA. / UN ESTUDIO, NO UNA VITRINA.", "Abre el espacio: invita a entrar antes de mostrar el oficio."),
    (6.00, "05", "5,40 – 6,60 s", "PLANO MEDIO", "35 mm · paneo", "CABINA CLÍNICA / AGUJAS SELLADAS", "Autoridad sanitaria: responde la objeción de higiene."),
    (7.20, "06", "6,60 – 7,80 s", "MACRO", "100 mm · push-in", "REALISMO / BLACK & GREY", "Especialidad declarada mientras se ve la técnica en vivo."),
    (8.40, "07", "7,80 – 9,00 s", "PLANO DETALLE", "50 mm · pull-back", "PIEZA ÚNICA / SIN PLANTILLAS", "Inicio del bloque de prueba: el resultado que se compra."),
    (9.60, "08", "9,00 – 10,20 s", "PLANO AMERICANO", "35 mm · planeo", "SIN PLANTILLAS / DISEÑADA PARA TI", "Refuerza exclusividad y diseño personalizado."),
    (10.80, "09", "10,20 – 11,40 s", "SPLIT · DOS MACROS", "100 mm · zoom cruzado", "TITANIO / ASTM F136", "Amplía la oferta a piercing con estándar verificable."),
    (12.00, "10", "11,40 – 12,60 s", "PLANO MEDIO", "35 mm · push-in + riser", "5 ARTISTAS / UN MISMO ESTÁNDAR", "Humaniza y cierra la fase de prueba antes del CTA."),
    (13.00, "11a", "12,60 – 13,60 s", "CIERRE · EMBLEMA", "pull-back + glow", "AGENDA TU HORA", "Hit de impacto: entra la marca y el llamado a la acción."),
    (14.30, "11b", "13,60 – 15,00 s", "CIERRE · CTA", "plano fijo", "WHATSAPP +56 9 4778 6839 / @abyss_tattoo_studio", "Una sola acción, número y dirección visibles hasta el último frame."),
]


def grab(t):
    p = f"/tmp/sb_{t:.2f}.png"
    if not os.path.exists(p):
        subprocess.run([FFMPEG, "-y", "-ss", str(t), "-i", MASTER, "-frames:v", "1", p],
                       check=True, stderr=subprocess.DEVNULL)
    return Image.open(p).convert("RGB")


def main():
    cw, ch = 340, 604          # imagen
    pad = 26
    col_w = cw + pad * 2
    row_h = ch + 210
    cols, rows = 4, 3
    W = col_w * cols + pad
    H = 190 + row_h * rows + pad
    sheet = Image.new("RGB", (W, H), OBSIDIAN)
    d = ImageDraw.Draw(sheet)

    d.text((pad + 8, 34), "STORYBOARD — REEL COMERCIAL 15 s", font=cin800, fill=PAPER)
    d.text((pad + 10, 88), "ABYSS TATTOO STUDIO · 1080×1920 · 60 fps · 100 BPM · cortes cada 0,60 s",
           font=m600, fill=BONE)
    d.line([(pad + 8, 126), (W - pad, 126)], fill=SAGE, width=2)
    d.text((pad + 8, 140), "HOOK 0–2,4 s   ·   CONTEXTO / AUTORIDAD 2,4–7,8 s   ·   PRUEBA 7,8–11,4 s   ·   EQUIPO 11,4–12,6 s   ·   CTA 12,6–15 s",
           font=m500, fill=TEAL_L)

    for i, (t, code, tc, plano, cam, copy, why) in enumerate(SHOTS):
        r, c = divmod(i, cols)
        x = pad + c * col_w
        y = 190 + r * row_h
        d.rounded_rectangle((x, y, x + col_w - pad, y + row_h - pad), radius=10, fill=PANEL,
                            outline=(58, 48, 42), width=1)
        img = grab(t).resize((cw, ch), Image.Resampling.LANCZOS)
        sheet.paste(img, (x + pad // 2, y + 14))
        d.rectangle((x + pad // 2, y + 14, x + pad // 2 + cw, y + 14 + ch), outline=(70, 60, 52))

        # código + timecode
        d.rectangle((x + pad // 2, y + 14, x + pad // 2 + 92, y + 52), fill=(12, 10, 9))
        d.text((x + pad // 2 + 12, y + 22), code, font=m700, fill=TEAL_L)
        d.rectangle((x + pad // 2 + cw - 132, y + 14, x + pad // 2 + cw, y + 52), fill=(12, 10, 9))
        d.text((x + pad // 2 + cw - 124, y + 24), tc.split(" – ")[0], font=m600, fill=BONE)

        ty = y + ch + 26
        d.text((x + pad // 2, ty), plano, font=m700, fill=PAPER)
        d.text((x + pad // 2, ty + 26), cam, font=m400, fill=TEAL_L)
        # copy en mayúsculas, envuelto
        words = copy.split()
        line, lines = "", []
        for w in words:
            probe = (line + " " + w).strip()
            if d.textlength(probe, font=m600) > cw - 4:
                lines.append(line)
                line = w
            else:
                line = probe
        lines.append(line)
        yy = ty + 54
        for ln in lines[:2]:
            d.text((x + pad // 2, yy), ln, font=m600, fill=CREAM)
            yy += 24
        # función comercial
        words, line, lines = why.split(), "", []
        for w in words:
            probe = (line + " " + w).strip()
            if d.textlength(probe, font=m400) > cw - 4:
                lines.append(line)
                line = w
            else:
                line = probe
        lines.append(line)
        yy += 6
        for ln in lines[:3]:
            d.text((x + pad // 2, yy), ln, font=m400, fill=(140, 128, 118))
            yy += 21

    sheet.save(OUT, quality=91)
    print("Storyboard:", OUT, sheet.size)


if __name__ == "__main__":
    main()
