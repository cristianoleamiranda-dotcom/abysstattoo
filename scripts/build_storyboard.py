#!/usr/bin/env python3
"""build_storyboard.py — Hoja de contacto / Storyboard técnico de los 12 planos del Reel Comercial 15s."""

import os
import shutil

import cv2
from PIL import Image, ImageDraw, ImageFont

ROOT = "/home/user/abysstattoo"
os.chdir(ROOT)

SRC = "film/reel_comercial_abyss_15s_1080x1920_60fps_social.mp4"
OUT = "film/storyboard_reel_abyss_15s.jpg"

BEATS = [
    (0.62, "01 · ECU MACRO · 100mm", "Video aguja real · Crash pull-back", "0.00 – 1.20 s"),
    (1.82, "02 · PRIMER PLANO · 50mm", "Video chiaroscuro · Punch zoom + whip X", "1.20 – 2.40 s"),
    (3.02, "03 · DRON FPV · 16mm", "Vuelo San Bernardo · J. J. Pérez 528", "2.40 – 3.60 s"),
    (4.08, "04 · FACHADA REAL · 24mm", "Foto verificada 528 · Dolly + tilt 3D", "3.60 – 4.50 s"),
    (4.96, "05 · TRAVELLING POV · 24mm", "Gimbal interior pasillo + whip Y", "4.50 – 5.40 s"),
    (6.02, "06 · PLANO CENITAL · 35mm", "Video cabina Seremi · Órbita picada", "5.40 – 6.60 s"),
    (7.24, "07 · PPP DETALLE · 85mm", "Video Ink Wipe HDR->SDR · Push-in", "6.60 – 7.80 s"),
    (8.12, "08 · REALISMO B&G · 50mm", "Corte al pulso · Zoom-in / Pull-back", "7.80 – 9.00 s"),
    (9.88, "09 · MANGA & COLOR · 35mm", "Tilt vertical + Whip Full Color", "9.00 – 10.20 s"),
    (10.82, "10 · DOBLE MACRO · 100mm", "Split-screen Titanio ASTM F136", "10.20 – 11.40 s"),
    (12.02, "11 · PLANO MEDIO · 50mm", "Video artista en cabina + Riser", "11.40 – 12.60 s"),
    (14.30, "12 · PACKSHOT CTA", "Emblema + WhatsApp +56 9 4778 6839 · 528", "12.60 – 15.00 s"),
]

COLS, ROWS = 6, 2
TW, TH = 315, 560
PAD, HEADER, CAP = 24, 118, 80
W = PAD * 2 + COLS * TW + (COLS - 1) * PAD
H = HEADER + ROWS * (TH + CAP) + (ROWS - 1) * PAD + PAD

f_title = ImageFont.truetype("assets/fonts/cinzel-800.ttf", 36)
f_sub = ImageFont.truetype("assets/fonts/montserrat-500.ttf", 16)
f_n = ImageFont.truetype("assets/fonts/montserrat-700.ttf", 14)
f_s = ImageFont.truetype("assets/fonts/montserrat-500.ttf", 13)
f_t = ImageFont.truetype("assets/fonts/montserrat-600.ttf", 12)

sheet = Image.new("RGB", (W, H), (20, 16, 13))
d = ImageDraw.Draw(sheet)
d.text((PAD, 28), "ABYSS TATTOO STUDIO — STORYBOARD REEL COMERCIAL 15 s (J. J. PÉREZ 528)", font=f_title, fill=(246, 241, 237))
d.text(
    (PAD, 76),
    "1080×1920 · 60 fps · BT.709 · 12 planos a 100 BPM (0.60 s/negra) · Rig virtual 3D sub-píxel · Audio estéreo 48 kHz · José Joaquín Pérez 528, San Bernardo",
    font=f_sub,
    fill=(181, 162, 149),
)
d.line([(PAD, HEADER - 10), (W - PAD, HEADER - 10)], fill=(85, 108, 101), width=2)

cap = cv2.VideoCapture(SRC)
vfps = cap.get(cv2.CAP_PROP_FPS) or 60.0

for i, (t, name, move, span) in enumerate(BEATS):
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(round(t * vfps)))
    ok, frame = cap.read()
    if not ok:
        continue
    im = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)).resize((TW, TH), Image.Resampling.LANCZOS)
    c, r = i % COLS, i // COLS
    x = PAD + c * (TW + PAD)
    y = HEADER + r * (TH + CAP + PAD)
    sheet.paste(im, (x, y))
    d.rectangle((x, y, x + TW - 1, y + TH - 1), outline=(92, 78, 68), width=1)
    d.text((x, y + TH + 8), name, font=f_n, fill=(246, 241, 237))
    d.text((x, y + TH + 30), move, font=f_s, fill=(181, 162, 149))
    d.text((x, y + TH + 50), span, font=f_t, fill=(158, 196, 186))

cap.release()
sheet.save(OUT, quality=93)
print(f"Storyboard guardado: {OUT} ({sheet.size})")
