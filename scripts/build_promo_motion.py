#!/usr/bin/env python3
"""Create a 10-second, silent 2.5D motion poster from the supplied Abyss promo image.

Run from the repository root with:
  .venv/bin/python scripts/build_promo_motion.py

The corrected lossless still is used as the foreground artwork. Motion comes
from a virtual perspective camera, a separately animated depth backdrop, eased
camera moves, a restrained warm light sweep, and small star glints.
"""

from __future__ import annotations

import argparse
import math
import subprocess
import sys
from pathlib import Path

import cv2
import imageio_ffmpeg
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "assets/promocion/abyss-promo-corrected.png"
DEFAULT_OUTPUT = ROOT / "film/abyss_promocion_motion_10s_1080x1920_60fps_hq.mp4"

WIDTH = 1080
HEIGHT = 1920
FPS = 60
DURATION = 10.0
CARD_WIDTH = 1060
CAMERA_DISTANCE = 2800.0
CAMERA_FOCAL = 2800.0

# (time, zoom, focus-x, focus-y, yaw-deg, pitch-deg, roll-deg)
# Focus coordinates are normalized on the original image. The close-up beats
# intentionally travel from the tattoo eyes down the three offer tiers.
CAMERA_KEYS = [
    (0.00, 0.92, 0.50, 0.50, -4.0, 2.2, -0.35),
    (0.68, 1.00, 0.50, 0.50, 1.3, -0.8, 0.15),
    (1.28, 1.03, 0.50, 0.48, 0.0, 0.0, 0.0),
    (2.20, 1.82, 0.73, 0.31, 0.2, -0.2, 0.05),
    (2.72, 1.82, 0.73, 0.31, 0.0, 0.0, 0.0),
    (3.70, 1.98, 0.24, 0.35, -0.08, 0.08, 0.0),
    (4.18, 1.98, 0.24, 0.35, 0.0, 0.0, 0.0),
    (5.05, 1.98, 0.23, 0.54, 0.0, 0.0, 0.0),
    (5.46, 1.98, 0.23, 0.54, 0.0, 0.0, 0.0),
    (6.34, 1.98, 0.22, 0.73, 0.0, 0.0, 0.0),
    (6.72, 1.98, 0.22, 0.73, 0.0, 0.0, 0.0),
    (7.82, 1.02, 0.50, 0.50, -0.2, 0.15, 0.0),
    (8.35, 1.00, 0.50, 0.50, 0.0, 0.0, 0.0),
    (9.72, 1.015, 0.50, 0.50, 0.0, 0.0, 0.0),
    (10.00, 1.00, 0.50, 0.50, 0.0, 0.0, 0.0),
]

# The four gold star dividers printed in the source artwork (source-pixel x, y).
STAR_POINTS = [(414, 363), (351, 691), (351, 991), (343, 1274)]


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def smoothstep(value: float) -> float:
    value = clamp01(value)
    return value * value * (3.0 - 2.0 * value)


def ease_between(t: float, t0: float, t1: float) -> float:
    if t1 <= t0:
        return 1.0
    return smoothstep((t - t0) / (t1 - t0))


def camera_at(t: float) -> tuple[float, ...]:
    for index in range(len(CAMERA_KEYS) - 1):
        a = CAMERA_KEYS[index]
        b = CAMERA_KEYS[index + 1]
        if t <= b[0]:
            p = ease_between(t, a[0], b[0])
            return tuple(a[i] + (b[i] - a[i]) * p for i in range(1, len(a)))
    return CAMERA_KEYS[-1][1:]


def build_background(source: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Create a soft, dark, oversized back plane with room for slow parallax."""
    source_h, source_w = source.shape[:2]
    resized_w = max(WIDTH + 150, int(round(source_w * HEIGHT / source_h)))
    background = cv2.resize(source, (resized_w, HEIGHT), interpolation=cv2.INTER_CUBIC)
    background = cv2.GaussianBlur(background, (0, 0), sigmaX=34, sigmaY=34)

    yy, xx = np.mgrid[0:HEIGHT, 0:WIDTH].astype(np.float32)
    dx = (xx - WIDTH * 0.50) / (WIDTH * 0.76)
    dy = (yy - HEIGHT * 0.48) / (HEIGHT * 0.65)
    radius = np.sqrt(dx * dx + dy * dy)
    vignette = np.clip(1.04 - 0.34 * radius * radius, 0.42, 1.0)
    # A quiet warm haze lifts the otherwise black ambience without competing
    # with the photograph or changing its artwork.
    glow = np.exp(-(((xx - WIDTH * 0.70) / 430.0) ** 2 + ((yy - HEIGHT * 0.53) / 680.0) ** 2))
    return background, (vignette * 0.34).astype(np.float32), glow.astype(np.float32)


def render_background(
    background: np.ndarray,
    vignette: np.ndarray,
    warm_glow: np.ndarray,
    t: float,
) -> np.ndarray:
    max_x = background.shape[1] - WIDTH
    center_x = max_x / 2.0
    drift = math.sin(t * 0.48) * 48.0 + math.sin(t * 0.19 + 0.7) * 20.0
    x0 = int(np.clip(round(center_x + drift), 0, max_x))
    crop = background[:, x0 : x0 + WIDTH].astype(np.float32)
    crop *= vignette[..., None]
    crop *= 0.31
    crop += np.array([7.0, 8.0, 10.0], dtype=np.float32)
    # OpenCV uses BGR. The low-amplitude gold haze sits well behind the card.
    crop += warm_glow[..., None] * np.array([2.0, 7.0, 15.0], dtype=np.float32)
    return np.clip(crop, 0, 255).astype(np.uint8)


def rotate_project(
    points: np.ndarray,
    image_center: tuple[float, float],
    scale: float,
    yaw_deg: float,
    pitch_deg: float,
    roll_deg: float,
) -> np.ndarray:
    """Project points from a flat image plane through a restrained 3D camera."""
    cx, cy = image_center
    local_x = (points[:, 0] - cx) * scale
    local_y = (points[:, 1] - cy) * scale
    local_z = np.zeros_like(local_x)

    yaw = math.radians(yaw_deg)
    pitch = math.radians(pitch_deg)
    roll = math.radians(roll_deg)

    x1 = math.cos(yaw) * local_x + math.sin(yaw) * local_z
    z1 = -math.sin(yaw) * local_x + math.cos(yaw) * local_z
    y2 = math.cos(pitch) * local_y - math.sin(pitch) * z1
    z2 = math.sin(pitch) * local_y + math.cos(pitch) * z1
    x3 = math.cos(roll) * x1 - math.sin(roll) * y2
    y3 = math.sin(roll) * x1 + math.cos(roll) * y2

    denominator = np.maximum(500.0, CAMERA_DISTANCE - z2)
    factor = CAMERA_FOCAL / denominator
    return np.column_stack((x3 * factor, y3 * factor)).astype(np.float32)


def get_card_transform(
    source_shape: tuple[int, ...],
    zoom: float,
    focus_x: float,
    focus_y: float,
    yaw: float,
    pitch: float,
    roll: float,
) -> tuple[np.ndarray, np.ndarray]:
    source_h, source_w = source_shape[:2]
    source_center = ((source_w - 1) * 0.5, (source_h - 1) * 0.5)
    scale = CARD_WIDTH / source_w * zoom
    corners = np.array(
        [[0, 0], [source_w - 1, 0], [source_w - 1, source_h - 1], [0, source_h - 1]],
        dtype=np.float32,
    )
    focus = np.array([[focus_x * (source_w - 1), focus_y * (source_h - 1)]], dtype=np.float32)
    projected_corners = rotate_project(corners, source_center, scale, yaw, pitch, roll)
    projected_focus = rotate_project(focus, source_center, scale, yaw, pitch, roll)[0]
    anchor = np.array([WIDTH * 0.5, HEIGHT * 0.5], dtype=np.float32)
    destinations = projected_corners - projected_focus + anchor
    matrix = cv2.getPerspectiveTransform(corners, destinations.astype(np.float32))
    return matrix, destinations


def warp_card(source: np.ndarray, matrix: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    warped = cv2.warpPerspective(
        source,
        matrix,
        (WIDTH, HEIGHT),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(0, 0, 0),
    )
    alpha = cv2.warpPerspective(
        np.full(source.shape[:2], 255, dtype=np.uint8),
        matrix,
        (WIDTH, HEIGHT),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=0,
    )
    return warped, alpha


def composite_card(
    frame: np.ndarray,
    source: np.ndarray,
    matrix: np.ndarray,
    destinations: np.ndarray,
    opacity: float,
    t: float,
) -> tuple[np.ndarray, np.ndarray]:
    warped, alpha_mask = warp_card(source, matrix)
    opacity = clamp01(opacity)

    # Drop shadow is a separate depth cue, offset away from the key light.
    shifted = cv2.warpAffine(
        alpha_mask,
        np.float32([[1, 0, 0], [0, 1, 18]]),
        (WIDTH, HEIGHT),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=0,
    )
    shadow = cv2.GaussianBlur(shifted, (0, 0), sigmaX=28, sigmaY=28).astype(np.float32) / 255.0
    frame = np.clip(frame.astype(np.float32) * (1.0 - shadow[..., None] * (0.38 * opacity)), 0, 255).astype(np.uint8)

    alpha = alpha_mask.astype(np.float32) / 255.0 * opacity
    frame = np.clip(
        frame.astype(np.float32) * (1.0 - alpha[..., None]) + warped.astype(np.float32) * alpha[..., None],
        0,
        255,
    ).astype(np.uint8)

    # Subtle antique-gold edge, consistent with the poster's printed rules.
    edge = np.zeros_like(frame)
    points = np.rint(destinations).astype(np.int32).reshape((-1, 1, 2))
    cv2.polylines(edge, [points], True, (89, 139, 180), 2, cv2.LINE_AA)
    edge_alpha = 0.23 * opacity
    frame = cv2.addWeighted(frame, 1.0, edge, edge_alpha, 0.0)

    # Two soft metallic sweeps, masked to the card so the fine copy remains legible.
    sweep = 0.0
    if 0.52 <= t <= 1.22:
        sweep = (t - 0.52) / (1.22 - 0.52)
    elif 8.68 <= t <= 9.55:
        sweep = (t - 8.68) / (9.55 - 8.68)
    if sweep > 0:
        yy, xx = np.mgrid[0:HEIGHT, 0:WIDTH].astype(np.float32)
        diagonal = xx + 0.29 * yy
        line_center = -0.35 * HEIGHT + sweep * (WIDTH + 0.64 * HEIGHT)
        streak = np.exp(-((diagonal - line_center) ** 2) / (2.0 * 19.0 * 19.0))
        streak *= alpha_mask.astype(np.float32) / 255.0
        streak *= 0.10 * opacity
        tint = np.array([104.0, 164.0, 215.0], dtype=np.float32)
        frame = np.clip(frame.astype(np.float32) * (1.0 - streak[..., None]) + tint * streak[..., None], 0, 255).astype(np.uint8)

    # Let the printed star separators catch a restrained, timed glint.
    flare_beats = [0.95, 3.92, 5.20, 6.48, 9.18]
    source_points = np.array(STAR_POINTS, dtype=np.float32).reshape((-1, 1, 2))
    projected_stars = cv2.perspectiveTransform(source_points, matrix).reshape((-1, 2))
    flare_strength = max(math.exp(-((t - beat) / 0.18) ** 2) for beat in flare_beats)
    if flare_strength > 0.015:
        for index, (x, y) in enumerate(projected_stars):
            if index == 0 and t > 2.0:
                continue
            if index == 1 and not 2.8 <= t <= 4.6 and t < 8.7:
                continue
            if index == 2 and not 4.2 <= t <= 5.9:
                continue
            if index == 3 and not 5.6 <= t <= 7.2:
                continue
            draw_star_glint(frame, float(x), float(y), flare_strength * opacity)

    return frame, alpha_mask


def draw_star_glint(frame: np.ndarray, x: float, y: float, strength: float) -> None:
    if x < -40 or x >= WIDTH + 40 or y < -40 or y >= HEIGHT + 40:
        return
    strength = clamp01(strength)
    if strength <= 0.005:
        return
    radius = 18
    x0, x1 = max(0, int(x) - radius), min(WIDTH, int(x) + radius + 1)
    y0, y1 = max(0, int(y) - radius), min(HEIGHT, int(y) + radius + 1)
    gy, gx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    dist2 = (gx - x) ** 2 + (gy - y) ** 2
    glow = np.exp(-dist2 / (2.0 * 6.2**2)) * (0.33 * strength)
    cross_x = np.exp(-((gy - y) ** 2) / (2.0 * 1.2**2)) * np.exp(-((gx - x) ** 2) / (2.0 * 14.0**2))
    cross_y = np.exp(-((gx - x) ** 2) / (2.0 * 1.2**2)) * np.exp(-((gy - y) ** 2) / (2.0 * 14.0**2))
    glow = np.clip(glow + (cross_x + cross_y) * (0.40 * strength), 0.0, 0.75)
    tint = np.array([158.0, 211.0, 250.0], dtype=np.float32)
    patch = frame[y0:y1, x0:x1].astype(np.float32)
    patch = patch * (1.0 - glow[..., None]) + tint * glow[..., None]
    frame[y0:y1, x0:x1] = np.clip(patch, 0, 255).astype(np.uint8)


def render_frame(
    source: np.ndarray,
    background: np.ndarray,
    vignette: np.ndarray,
    warm_glow: np.ndarray,
    t: float,
) -> np.ndarray:
    frame = render_background(background, vignette, warm_glow, t)
    zoom, focus_x, focus_y, yaw, pitch, roll = camera_at(t)
    matrix, destinations = get_card_transform(source.shape, zoom, focus_x, focus_y, yaw, pitch, roll)
    reveal = ease_between(t, 0.0, 0.56)
    fadeout = 1.0 - ease_between(t, 9.72, 10.0)
    opacity = reveal * fadeout
    frame, _ = composite_card(frame, source, matrix, destinations, opacity, t)

    # A restrained edge frame and drifting dust create a foreground layer.
    # They are purposefully low contrast so the offer and tattoo remain primary.
    frame_marks = np.zeros_like(frame)
    gold = (49, 86, 117)
    cv2.line(frame_marks, (42, 308), (42, 500), gold, 1, cv2.LINE_AA)
    cv2.line(frame_marks, (1038, 308), (1038, 500), gold, 1, cv2.LINE_AA)
    cv2.line(frame_marks, (42, 1420), (42, 1610), gold, 1, cv2.LINE_AA)
    cv2.line(frame_marks, (1038, 1420), (1038, 1610), gold, 1, cv2.LINE_AA)
    frame = cv2.addWeighted(frame, 1.0, frame_marks, 0.18 * opacity, 0.0)

    global_fade = min(reveal, fadeout)
    if global_fade < 1.0:
        frame = np.clip(frame.astype(np.float32) * global_fade, 0, 255).astype(np.uint8)
    return frame


def make_video(source_path: Path, output_path: Path, fps: int = FPS, duration: float = DURATION) -> None:
    source = cv2.imread(str(source_path), cv2.IMREAD_COLOR)
    if source is None:
        raise FileNotFoundError(f"No pude leer la imagen fuente: {source_path}")
    if source.shape[0] < 800 or source.shape[1] < 800:
        raise ValueError("La imagen fuente debe tener al menos 800 px por lado para un master social nítido.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    background, vignette, warm_glow = build_background(source)
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    command = [
        ffmpeg,
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-f",
        "rawvideo",
        "-vcodec",
        "rawvideo",
        "-s",
        f"{WIDTH}x{HEIGHT}",
        "-pix_fmt",
        "bgr24",
        "-r",
        str(fps),
        "-i",
        "-",
        "-an",
        "-c:v",
        "libx264",
        "-preset",
        "slow",
        "-crf",
        "14",
        "-profile:v",
        "high",
        "-level:v",
        "4.2",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        "-color_primaries",
        "bt709",
        "-color_trc",
        "bt709",
        "-colorspace",
        "bt709",
        "-metadata",
        "title=Abyss Tattoo Studio - 2.5D Motion Poster",
        str(output_path),
    ]

    total_frames = int(round(fps * duration))
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        assert process.stdin is not None
        for index in range(total_frames):
            # Retiming duration changes speed, not the authored sequence or its ending.
            t = index / max(1, total_frames - 1) * DURATION
            frame = render_frame(source, background, vignette, warm_glow, t)
            process.stdin.write(frame.tobytes())
            if (index + 1) % fps == 0 or index + 1 == total_frames:
                print(f"Render: {index + 1}/{total_frames} frames", flush=True)
        process.stdin.close()
        stderr = process.stderr.read() if process.stderr is not None else b""
        return_code = process.wait()
    except BaseException:
        process.kill()
        process.wait()
        raise

    if return_code != 0:
        raise RuntimeError(f"FFmpeg no pudo crear el MP4: {stderr.decode('utf-8', errors='replace')}")

    size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"MP4 listo: {output_path.relative_to(ROOT)} ({size_mb:.1f} MB)")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE, help="JPEG/PNG original")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="MP4 vertical de salida")
    parser.add_argument("--fps", type=int, default=FPS, help="Cuadros por segundo (default: 30)")
    parser.add_argument("--duration", type=float, default=DURATION, help="Duración en segundos (default: 10)")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.fps < 24 or args.fps > 60:
        raise SystemExit("El FPS debe estar entre 24 y 60.")
    if not 6.0 <= args.duration <= 30.0:
        raise SystemExit("La duración debe estar entre 6 y 30 segundos.")
    source = args.source if args.source.is_absolute() else ROOT / args.source
    output = args.output if args.output.is_absolute() else ROOT / args.output
    make_video(source, output, args.fps, args.duration)
    return 0


if __name__ == "__main__":
    sys.exit(main())
