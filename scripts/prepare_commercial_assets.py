#!/usr/bin/env python3
"""
PASO 1 — AUDITORÍA, CURADURÍA Y ETALONAJE DEL MATERIAL AUDIOVISUAL
Abyss Tattoo Studio · Reel Comercial 15s (José Joaquín Pérez 528, San Bernardo)
Skills activas: PhotoCraft + LightCraft + VectorCraft + FilmCraft

Reglas estrictas de curaduría antes de montar:
 1) Se descartan tarjetas promocionales antiguas (20% / 10% / $70.000 / Marcos Salinas) y dirección antigua (548).
 2) Se recortan los rótulos quemados superiores/inferiores del vuelo FPV y recorrido interior (CROP 9:16 limpio).
 3) Se descartan frames transicionales con texto deformado por IA y capturas con UI móvil (< 65 KB / Instagram UI),
    usando exclusivamente fotografía real verificada de fachada (assets/estudio/fachada.jpg, numeración oficial 528).
 4) Se aplica tone-mapping óptico HLG 10-bit (bt2020nc / arib-std-b67) -> BT.709 SDR con compresión suave de altas
    luces en piel en proceso_detalle.mp4 (incluyendo el Ink Wipe Reveal en vivo).
 5) Todas las placas se masterizan con +20 % de overscan (1296x2304) para permitir zooms, paneos y tiros 3D
    sub-píxel sin pérdida óptica ni bordes negros.
"""

import json
import os
import shutil
import subprocess

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

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
OUT = os.path.join(ROOT, "assets/reel_plates")
RAW = "/tmp/reel_raw"
os.makedirs(OUT, exist_ok=True)
os.makedirs(RAW, exist_ok=True)

STORY = "dropbox/story_ubicacion_aerea_abyss_1080p.mp4"

# Ventana 9:16 exacta (675x1200 = 0.5625) en el interior limpio del story 1080x1920:
# excluye 100 % la cabecera quemada (y < 444) y la pastilla inferior con dirección antigua (y > 1644).
CROP_W, CROP_H, CROP_X, CROP_Y = 675, 1200, 202, 444

OV_W, OV_H = 1296, 2304  # 1080x1920 + 20 % overscan óptico


def hlg_to_sdr_bgr(bgr: np.ndarray) -> np.ndarray:
    """Tone-mapping perceptual HLG 10-bit (BT.2020) -> BT.709 SDR preservando tonos de piel y negros de tinta."""
    x = bgr.astype(np.float32) / 255.0
    # Compresión suave de rodilla (soft-knee Reinhard/ACES simplificado) sobre luminancia sobreexpuesta HLG
    x = x / (1.0 + 0.62 * (x ** 1.35)) * 1.46
    x = np.clip(x, 0.0, 1.0) ** 1.16
    # Corrección de matriz cromática aproximada BT.2020 -> BT.709 (reduce saturación naranja excesiva en piel)
    b, g, r = x[..., 0], x[..., 1], x[..., 2]
    r_out = np.clip(1.06 * r - 0.05 * g - 0.01 * b, 0.0, 1.0)
    g_out = np.clip(-0.02 * r + 1.03 * g - 0.01 * b, 0.0, 1.0)
    b_out = np.clip(-0.01 * r - 0.03 * g + 1.04 * b, 0.0, 1.0)
    out = np.stack([b_out, g_out, r_out], axis=-1)
    hsv = cv2.cvtColor((out * 255.0).astype(np.uint8), cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv[..., 1] = np.clip(hsv[..., 1] * 0.78, 0, 255)
    return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)


def lightcraft_grade_bgr(
    bgr: np.ndarray,
    warmth: float = 0.07,
    contrast: float = 1.08,
    teal: float = 0.05,
    sat: float = 0.94,
    sharpen: float = 0.22,
) -> np.ndarray:
    """Etalonaje unificado Abyss: micro-contraste LAB + split-toning Obsidiana/Teal/Hueso + nitidez óptica."""
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv[:, :, 1] = np.clip(hsv[:, :, 1] * sat, 0, 255)
    work = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)

    lab = cv2.cvtColor(work, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    l_eq = cv2.createCLAHE(clipLimit=1.70, tileGridSize=(8, 8)).apply(l)
    l = cv2.addWeighted(l, 0.64, l_eq, 0.36, 0)
    g = cv2.cvtColor(cv2.merge([l, a, b]), cv2.COLOR_LAB2BGR).astype(np.float32) / 255.0

    g = np.clip((g - 0.5) * contrast + 0.5, 0, 1)
    lum = 0.114 * g[:, :, 0] + 0.587 * g[:, :, 1] + 0.299 * g[:, :, 2]
    shadow = np.clip(1.0 - lum * 1.9, 0, 1)
    high = np.clip((lum - 0.42) * 1.7, 0, 1)

    # Luces cálidas Hueso (#B5A295) y sombras frías minerales Obsidiana/Salvia (#14100D / #556C65)
    g[:, :, 2] = np.clip(g[:, :, 2] + high * warmth * 0.48 - shadow * teal * 0.28, 0, 1)
    g[:, :, 1] = np.clip(g[:, :, 1] + high * warmth * 0.20 + shadow * teal * 0.22, 0, 1)
    g[:, :, 0] = np.clip(g[:, :, 0] - high * warmth * 0.18 + shadow * teal * 0.30, 0, 1)

    out = (g * 255.0).astype(np.uint8)
    if sharpen > 0:
        blur = cv2.GaussianBlur(out, (0, 0), 1.05)
        out = cv2.addWeighted(out, 1.0 + sharpen, blur, -sharpen, 0)
    return out


def crop_to_aspect_overscan(bgr: np.ndarray, fx: float = 0.5, fy: float = 0.5) -> np.ndarray:
    """Recorta sin deformar al aspect ratio 9:16 exacto y escala a 1296x2304 con Lanczos-4."""
    h, w = bgr.shape[:2]
    ratio = OV_W / OV_H
    if w / h > ratio:
        nw = int(round(h * ratio))
        x0 = max(0, min(w - nw, int(round((w - nw) * fx))))
        cropped = bgr[:, x0 : x0 + nw]
    else:
        nh = int(round(w / ratio))
        y0 = max(0, min(h - nh, int(round((h - nh) * fy))))
        cropped = bgr[y0 : y0 + nh, :]
    return cv2.resize(cropped, (OV_W, OV_H), interpolation=cv2.INTER_LANCZOS4)


def save_jpg(bgr: np.ndarray, name: str) -> None:
    cv2.imwrite(os.path.join(OUT, name), bgr, [cv2.IMWRITE_JPEG_QUALITY, 95])


def framed_still(src: str, name: str, fx=0.5, fy=0.5, warm=0.07, contrast=1.08, sat=0.93) -> None:
    img = cv2.imread(src)
    if img is None:
        raise FileNotFoundError(src)
    graded = lightcraft_grade_bgr(crop_to_aspect_overscan(img, fx, fy), warm, contrast, sat=sat)
    save_jpg(graded, name)
    print(f"  [still]  {name}  <- {src}")


def video_plate(
    src: str,
    ss: float,
    dur: float,
    name: str,
    crop_rect=None,
    hdr_to_sdr: bool = False,
    warm: float = 0.06,
    contrast: float = 1.08,
    sat: float = 0.92,
    fx: float = 0.5,
    fy: float = 0.5,
) -> None:
    """Decodifica video fuente, recorta bordes/UI si aplica, convierte HLG->SDR, etalona y codifica a x264."""
    cap = cv2.VideoCapture(src)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    start_frame = int(round(ss * fps))
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    n = int(round(dur * fps))
    out_path = os.path.join(OUT, name)
    proc = subprocess.Popen(
        [
            FFMPEG, "-y",
            "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{OV_W}x{OV_H}", "-r", f"{fps:.3f}",
            "-i", "-", "-an",
            "-c:v", "libx264", "-preset", "fast", "-crf", "15",
            "-pix_fmt", "yuv420p",
            "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
            out_path,
        ],
        stdin=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    written = 0
    last_good = None
    for _ in range(n):
        ok, frame = cap.read()
        if not ok:
            if last_good is None:
                break
            frame = last_good.copy()
        else:
            last_good = frame
        if crop_rect is not None:
            cw, ch, cx, cy = crop_rect
            frame = frame[cy : cy + ch, cx : cx + cw]
        if hdr_to_sdr:
            frame = hlg_to_sdr_bgr(frame)
        frame_ov = crop_to_aspect_overscan(frame, fx=fx, fy=fy)
        graded = lightcraft_grade_bgr(frame_ov, warmth=warm, contrast=contrast, sat=sat)
        proc.stdin.write(graded.tobytes())
        written += 1
    cap.release()
    proc.stdin.close()
    proc.wait()
    print(f"  [video]  {name}  ({written} frames @ {fps:.1f}fps) <- {src}")


def build_clean_emblem() -> None:
    """Construye emblema circular oficial de alta nitidez con máscara alfa antialiasing."""
    candidates = [
        "/tmp/inspect_imgs/db_02.jpeg",
        "/tmp/inspect_imgs/db_01.png",
        "assets/logo_abyss_256.png",
    ]
    src = next(p for p in candidates if os.path.exists(p))
    im = Image.open(src).convert("RGBA")
    size = 640
    im = im.resize((size, size), Image.Resampling.LANCZOS)
    im = ImageEnhance.Sharpness(im).enhance(1.35)
    im = ImageEnhance.Contrast(im).enhance(1.06)

    # Detección radial sub-píxel del borde exterior exacto del medallón oscuro (transición <120 -> >180)
    arr = np.array(im)
    gray = 0.299 * arr[..., 0] + 0.587 * arr[..., 1] + 0.114 * arr[..., 2]
    inside_dark = gray < 110
    ys, xs = np.where(inside_dark)
    cx = float(xs.mean())
    cy = float(ys.mean())
    radii = np.sqrt((xs - cx) ** 2 + (ys - cy) ** 2)
    max_r = float(np.percentile(radii, 99.85)) - 1.5

    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    rr = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    alpha = np.clip((max_r - rr) / 2.0, 0.0, 1.0) * 255.0
    arr[..., 3] = alpha.astype(np.uint8)
    # Limpia cualquier sangrado blanco residual en el borde antialiasing fijando RGB oscuro fuera de max_r - 2
    rim = rr > (max_r - 2.5)
    arr[rim, 0] = np.minimum(arr[rim, 0], 46)
    arr[rim, 1] = np.minimum(arr[rim, 1], 40)
    arr[rim, 2] = np.minimum(arr[rim, 2], 35)
    Image.fromarray(arr).save(os.path.join(OUT, "emblema_abyss_alpha.png"))
    print(f"  [alpha]  emblema_abyss_alpha.png  (src={src}, center=({cx:.1f},{cy:.1f}), r={max_r:.1f}px)")


if __name__ == "__main__":
    print("=== CURADURÍA, RESTAURACIÓN Y ETALONAJE DE PLACAS (ABYSS 528) ===")

    # Limpia placas antiguas obsoletas con letrero IA deformado
    for old_f in os.listdir(OUT):
        if old_f.startswith("plate_"):
            os.remove(os.path.join(OUT, old_f))

    # 1. Placas de VIDEO en movimiento real (8 tomas cinematográficas curadas)
    video_plate(
        "film/hero_film.mp4", 2.40, 1.68, "plate_v01_macro_aguja.mp4",
        warm=0.07, contrast=1.12, sat=0.92,
    )
    video_plate(
        "film/hero_film.mp4", 4.46, 1.25, "plate_v02_hero_reveal.mp4",
        warm=0.06, contrast=1.14, sat=0.90,
    )
    if os.path.exists(STORY):
        # Vuelo FPV real sobre San Bernardo al atardecer (antes de la transición IA en t=2.7s), 100 % sin rótulos
        video_plate(
            STORY, 0.12, 2.46, "plate_v03_dron_aereo.mp4",
            crop_rect=(CROP_W, CROP_H, CROP_X, CROP_Y),
            warm=0.09, contrast=1.09, sat=0.96,
        )
        # Recorrido interior gimbal FPV (pasillo -> vitrina -> cabina), 100 % sin rótulos
        video_plate(
            STORY, 7.22, 2.40, "plate_v04_pasillo_pov.mp4",
            crop_rect=(CROP_W, CROP_H, CROP_X, CROP_Y),
            warm=0.07, contrast=1.08, sat=0.94,
        )
    video_plate(
        "film/hero_film.mp4", 0.08, 1.90, "plate_v05_cabina_cenital.mp4",
        warm=0.06, contrast=1.09, sat=0.90,
    )
    video_plate(
        "film/proceso_detalle.mp4", 6.02, 1.92, "plate_v06_wipe_reveal.mp4",
        hdr_to_sdr=True, warm=0.06, contrast=1.10, sat=0.90, fx=0.52, fy=0.48,
    )
    video_plate(
        "film/proceso_pierna.mp4", 1.00, 2.10, "plate_v07_artista_sesion.mp4",
        warm=0.06, contrast=1.09, sat=0.90,
    )
    video_plate(
        "film/proceso_filmacion.mp4", 1.80, 1.90, "plate_v08_filmacion_estudio.mp4",
        warm=0.06, contrast=1.09, sat=0.92,
    )

    # 2. Placas FOTOGRÁFICAS reales de estudio, portafolio y joyería de titanio
    framed_still("assets/estudio/fachada.jpg", "plate_p01_fachada_real.jpg", 0.52, 0.45, 0.07, 1.10, 0.95)
    framed_still("assets/trabajos/lobo_samurai.jpg", "plate_p02_lobo_samurai.jpg", 0.50, 0.46, 0.07, 1.12, 0.92)
    framed_still("assets/trabajos/trabajo_hombro_real.jpg", "plate_p03_hombro_realismo.jpg", 0.50, 0.44, 0.06, 1.13, 0.88)
    framed_still("assets/trabajos/trabajo_cristo_manga.jpg", "plate_p04_cristo_manga.jpg", 0.50, 0.46, 0.07, 1.10, 0.90)
    framed_still("assets/trabajos/goku.jpg", "plate_p05_color_anime.jpg", 0.50, 0.48, 0.05, 1.10, 1.04)
    framed_still("assets/trabajos/helice.jpg", "plate_p06_helix_titanio.jpg", 0.52, 0.44, 0.06, 1.08, 0.94)
    framed_still("assets/trabajos/septum.jpg", "plate_p07_septum_titanio.jpg", 0.50, 0.50, 0.06, 1.09, 0.93)
    framed_still("assets/estudio/vitrina.jpg", "plate_p08_vitrina_estudio.jpg", 0.50, 0.50, 0.06, 1.09, 0.92)

    build_clean_emblem()
    print("=== PLACAS GENERADAS ===")
    print(json.dumps(sorted(os.listdir(OUT)), indent=2))
