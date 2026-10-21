#!/usr/bin/env python3
"""
PASO 1 — AUDITORÍA, CURADURÍA Y ETALONAJE DEL MATERIAL AUDIOVISUAL
Abyss Tattoo Studio · Reel Comercial 15s · PhotoCraft + LightCraft + VectorCraft

Ningún activo entra a la línea de tiempo en crudo:
 1) Se descartan las tarjetas promocionales antiguas (20% / 10% / $70.000) y los rótulos obsoletos.
 2) Se recortan los rótulos quemados del story aéreo y el marco del template vertical.
 3) Se reencuadra a 9:16 con overscan 1296x2304 (+20%) para permitir zoom, paneo y giro sin bordes.
 4) Tone-mapping HDR HLG (BT.2020) -> BT.709 y etalonaje unificado LightCraft en cada fotograma.

Salidas en assets/reel_plates/:
  plate_sXX_*.jpg   fotogramas curados del story (dron, fachada, pasillo, vitrina, escalera, cabina)
  plate_pXX_*.jpg   fotografía de estudio y portafolio reencuadrada y etalonada
  plate_vXX_*.mp4   placas de video 1296x2304 @ 30 fps etalonadas
  emblema_abyss_alpha.png  emblema oficial circular con alfa
"""

import json
import os
import subprocess

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = "/home/user/abysstattoo"
os.chdir(ROOT)
FFMPEG = f"{ROOT}/.venv/bin/ffmpeg"
OUT = f"{ROOT}/assets/reel_plates"
RAW = "/tmp/reel_raw"
os.makedirs(OUT, exist_ok=True)
os.makedirs(RAW, exist_ok=True)

STORY = "dropbox/story_ubicacion_aerea_abyss_1080p.mp4"

# Interior fotográfico del story: dentro de él se toma un 9:16 limpio, sin cabecera,
# sin numeración desactualizada ni pastilla inferior del template anterior.
CROP_W, CROP_H, CROP_X, CROP_Y = 675, 1200, 202, 420

OV_W, OV_H = 1296, 2304          # 1080x1920 + 20% de overscan


def lightcraft_grade_bgr(bgr, warmth=0.07, contrast=1.07, teal=0.05, sat=0.94, sharpen=0.20):
    """Micro-contraste LAB + split-toning Obsidiana/Teal/Hueso + enfoque óptico suave."""
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv[:, :, 1] = np.clip(hsv[:, :, 1] * sat, 0, 255)
    work = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)

    lab = cv2.cvtColor(work, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    l_eq = cv2.createCLAHE(clipLimit=1.75, tileGridSize=(8, 8)).apply(l)
    l = cv2.addWeighted(l, 0.62, l_eq, 0.38, 0)
    g = cv2.cvtColor(cv2.merge([l, a, b]), cv2.COLOR_LAB2BGR).astype(np.float32) / 255.0

    g = np.clip((g - 0.5) * contrast + 0.5, 0, 1)
    lum = 0.114 * g[:, :, 0] + 0.587 * g[:, :, 1] + 0.299 * g[:, :, 2]
    shadow = np.clip(1.0 - lum * 1.9, 0, 1)
    high = np.clip((lum - 0.42) * 1.7, 0, 1)

    g[:, :, 2] = np.clip(g[:, :, 2] + high * warmth * 0.50 - shadow * teal * 0.30, 0, 1)
    g[:, :, 1] = np.clip(g[:, :, 1] + high * warmth * 0.22 + shadow * teal * 0.22, 0, 1)
    g[:, :, 0] = np.clip(g[:, :, 0] - high * warmth * 0.18 + shadow * teal * 0.30, 0, 1)

    out = (g * 255.0).astype(np.uint8)
    if sharpen:
        blur = cv2.GaussianBlur(out, (0, 0), 1.1)
        out = cv2.addWeighted(out, 1 + sharpen, blur, -sharpen, 0)
    return out


def to_overscan(bgr):
    return cv2.resize(bgr, (OV_W, OV_H), interpolation=cv2.INTER_LANCZOS4)


def save_jpg(bgr, name):
    cv2.imwrite(os.path.join(OUT, name), bgr, [cv2.IMWRITE_JPEG_QUALITY, 95])


def story_still(t, name, warm=0.08, contrast=1.08, sat=0.95):
    raw = f"{RAW}/{name}.png"
    subprocess.run([FFMPEG, "-y", "-ss", str(t), "-i", STORY, "-frames:v", "1",
                    "-vf", f"crop={CROP_W}:{CROP_H}:{CROP_X}:{CROP_Y}", raw],
                   check=True, stderr=subprocess.DEVNULL)
    img = cv2.imread(raw)
    save_jpg(lightcraft_grade_bgr(to_overscan(img), warm, contrast, sat=sat), name)
    print("  still story →", name)


def framed_still(src, name, fx=0.5, fy=0.5, warm=0.07, contrast=1.08, sat=0.93):
    img = cv2.imread(src)
    h, w = img.shape[:2]
    ratio = OV_W / OV_H
    if w / h > ratio:
        nw = int(round(h * ratio))
        x0 = int(round((w - nw) * fx))
        img = img[:, x0:x0 + nw]
    else:
        nh = int(round(w / ratio))
        y0 = int(round((h - nh) * fy))
        img = img[y0:y0 + nh, :]
    save_jpg(lightcraft_grade_bgr(to_overscan(img), warm, contrast, sat=sat), name)
    print("  still foto  →", name)


def video_plate(src, ss, dur, name, hdr_to_sdr=False):
    """Decodifica con OpenCV, reencuadra, etalona fotograma a fotograma y escribe por tubería a x264."""
    cap = cv2.VideoCapture(src)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    cap.set(cv2.CAP_PROP_POS_MSEC, ss * 1000.0)
    n = int(round(dur * fps))
    proc = subprocess.Popen([
        FFMPEG, "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{OV_W}x{OV_H}", "-r", f"{fps:.3f}",
        "-i", "-", "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "16",
        "-pix_fmt", "yuv420p", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
        os.path.join(OUT, name)
    ], stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
    for _ in range(n):
        ok, frame = cap.read()
        if not ok:
            break
        frame = to_overscan(frame)
        if hdr_to_sdr:
            frame = cv2.convertScaleAbs(frame, alpha=1.02, beta=-6)
        proc.stdin.write(lightcraft_grade_bgr(frame, 0.06, 1.08, sat=0.90).tobytes())
    cap.release()
    proc.stdin.close()
    proc.wait()
    print("  video plate →", name)


def emblem_alpha():
    src = "/tmp/extracted_db/db_img_03.png"
    if not os.path.exists(src):
        src = "assets/logo_abyss_256.png"
    im = Image.open(src).convert("RGBA")
    size = 640
    im = im.resize((size, size), Image.Resampling.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((6, 6, size - 6, size - 6), fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(1.4))
    r, g, b, a = im.split()
    im.putalpha(Image.composite(a, Image.new("L", (size, size), 0), mask))
    im.save(os.path.join(OUT, "emblema_abyss_alpha.png"))
    print("  emblema con alfa → emblema_abyss_alpha.png")


if __name__ == "__main__":
    print("→ Fotogramas curados del story aéreo / recorrido del estudio")
    story_still(1.00, "plate_s01_dron.jpg")
    story_still(3.55, "plate_s02_fachada_noche.jpg")
    story_still(4.90, "plate_s03_fachada_dia.jpg")
    story_still(8.05, "plate_s04_pasillo.jpg")
    story_still(9.05, "plate_s05_vitrina.jpg")
    story_still(10.05, "plate_s06_escalera.jpg")
    story_still(11.05, "plate_s07_cabina.jpg")

    print("→ Fotografía de estudio y portafolio reencuadrada")
    framed_still("assets/estudio/maestro.jpg", "plate_p01_maestro.jpg", 0.5, 0.42, 0.06, 1.10, 0.90)
    framed_still("assets/trabajos/lobo_samurai.jpg", "plate_p02_lobo.jpg", 0.5, 0.46, 0.07, 1.12, 0.92)
    framed_still("assets/trabajos/trabajo_hombro_real.jpg", "plate_p03_hombro.jpg", 0.5, 0.44, 0.06, 1.13, 0.88)
    framed_still("assets/trabajos/trabajo_cristo_manga.jpg", "plate_p04_cristo.jpg", 0.5, 0.46, 0.07, 1.10, 0.90)
    framed_still("assets/trabajos/goku.jpg", "plate_p05_color.jpg", 0.5, 0.48, 0.05, 1.09, 1.03)
    framed_still("assets/trabajos/helice.jpg", "plate_p06_helix.jpg", 0.52, 0.44, 0.06, 1.08, 0.94)
    framed_still("assets/trabajos/septum.jpg", "plate_p07_septum.jpg", 0.5, 0.5, 0.06, 1.09, 0.93)
    framed_still("assets/trabajos/trabajo_lobo_rugido.jpg", "plate_p08_lobo2.jpg", 0.5, 0.46, 0.07, 1.11, 0.90)

    print("→ Placas de video etalonadas (incluye HLG/10-bit → BT.709)")
    video_plate(STORY, 0.10, 3.10, "plate_v01_dron.mp4")
    video_plate("film/hero_film.mp4", 0.05, 1.85, "plate_v02_cabina.mp4")
    video_plate("film/hero_film.mp4", 2.10, 1.70, "plate_v03_macro.mp4")
    video_plate("film/proceso_detalle.mp4", 1.60, 2.40, "plate_v04_sombreado.mp4", hdr_to_sdr=True)
    video_plate("film/proceso_filmacion.mp4", 1.40, 2.60, "plate_v05_manga.mp4")
    video_plate("film/proceso_pierna.mp4", 0.70, 2.20, "plate_v06_sesion.mp4")

    emblem_alpha()
    print(json.dumps(sorted(os.listdir(OUT)), indent=1))
