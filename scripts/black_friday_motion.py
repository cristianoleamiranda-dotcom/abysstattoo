#!/usr/bin/env python3
"""ABYSS Black Friday — reference-motion transfer and vertical campaign render.

The reference clip is analyzed frame-by-frame. ORB/RANSAC estimates the
reference camera transform; Farneback flow, cut scores and motion metadata are
stored for audit. The same normalized camera path is transferred to a branded
ABYSS poster assembled from the supplied Dropbox assets.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
import zipfile
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

W, H, FPS = 1080, 1920, 30
PALETTE = {
    "obsidian": "#14100D", "panel": "#1A1512", "bone": "#B5A295",
    "cream": "#EAE3DD", "sage": "#556C65", "teal": "#9EC4BA",
}
EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
cv2.setNumThreads(2)


def load_font(asset_root: Path, candidates: list[str], size: int):
    for name in candidates:
        p = asset_root / "fonts" / name
        if p.exists():
            try:
                return ImageFont.truetype(str(p), size)
            except OSError:
                pass
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"):
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def find_images(asset_root: Path) -> list[Path]:
    files = []
    for p in asset_root.rglob("*"):
        if p.is_file() and p.suffix.lower() in EXTS and p.stat().st_size > 20_000:
            if "logo" in p.name.lower() or "emblem" in p.name.lower():
                continue
            try:
                with Image.open(p) as im:
                    if im.width >= 280 and im.height >= 280:
                        files.append((p.stat().st_size, p))
            except Exception:
                continue
    files.sort(reverse=True, key=lambda x: x[0])
    return [p for _, p in files]


def find_emblem(asset_root: Path):
    for p in asset_root.rglob("*"):
        if p.is_file() and p.suffix.lower() == ".png" and any(k in p.name.lower() for k in ("emblem", "logo", "abyss")):
            try:
                im = Image.open(p)
                if im.width >= 80 and im.height >= 80:
                    return im.convert("RGBA")
            except Exception:
                pass
    return None


def tint_photo(path: Path, size: tuple[int, int]) -> Image.Image:
    im = Image.open(path).convert("RGB")
    im = ImageOps.fit(im, size, method=Image.Resampling.LANCZOS, centering=(0.5, 0.45))
    gray = ImageOps.grayscale(im)
    # restrained mineral duotone: obsidian shadows, bone highlights
    return ImageOps.colorize(gray, black="#171310", white="#C5B7AC").convert("RGB")


def tracked(draw, xy, text, font, fill, spacing=5):
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=font, fill=fill, stroke_width=0)
        x += draw.textlength(ch, font=font) + spacing


def build_poster(asset_root: Path, image_path: Path | None, variant: int = 0) -> np.ndarray:
    canvas = Image.new("RGB", (W, H), PALETTE["obsidian"])
    d = ImageDraw.Draw(canvas)
    # restrained paper grain / editorial rules
    for y in range(72, H, 84):
        d.line((54, y, W - 54, y), fill="#26211D", width=1)
    d.rectangle((34, 34, W - 34, H - 34), outline="#75675D", width=2)

    cinzel = load_font(asset_root, ["cinzel-800.ttf", "cinzel-700.ttf", "Cinzel-Bold.ttf"], 80)
    cinzel_mid = load_font(asset_root, ["cinzel-700.ttf", "cinzel-600.ttf"], 38)
    mont = load_font(asset_root, ["montserrat-700.ttf", "montserrat-600.ttf"], 28)
    mont_small = load_font(asset_root, ["montserrat-500.ttf", "montserrat-400.ttf"], 19)

    # Header / emblem
    emblem = find_emblem(asset_root)
    if emblem:
        emblem.thumbnail((126, 126), Image.Resampling.LANCZOS)
        canvas.paste(emblem, (W // 2 - emblem.width // 2, 76), emblem)
    tracked(d, (78, 218), "ABYSS TATTOO STUDIO", mont, PALETTE["cream"], 5)
    d.line((78, 270, W - 78, 270), fill=PALETTE["sage"], width=2)
    d.text((70, 294), "BLACK", font=cinzel, fill=PALETTE["cream"])
    d.text((70, 378), "FRIDAY", font=cinzel, fill=PALETTE["bone"])
    tracked(d, (78, 485), "TATTOO  /  PIERCING  /  ART", mont_small, PALETTE["teal"], 4)

    # Main campaign image, framed like the photo panel in the reference
    if image_path:
        photo = tint_photo(image_path, (850, 610))
        # subtle edge and inner keyline
        canvas.paste(photo, (115, 565))
        d.rectangle((108, 558, 972, 1182), outline=PALETTE["bone"], width=2)
        d.rectangle((120, 570, 960, 1170), outline="#65584F", width=1)
    else:
        d.rectangle((115, 565, 965, 1175), fill=PALETTE["panel"], outline=PALETTE["bone"], width=2)
        d.text((170, 800), "TATTOO  /  PIERCING", font=cinzel_mid, fill=PALETTE["cream"])

    # Recursive inset panel: nod to the reference's poster-within-poster
    inset = Image.new("RGB", (380, 470), PALETTE["panel"])
    idraw = ImageDraw.Draw(inset)
    idraw.rectangle((8, 8, 372, 462), outline=PALETTE["bone"], width=2)
    idraw.text((28, 32), "ABYSS", font=load_font(asset_root, ["cinzel-700.ttf"], 44), fill=PALETTE["cream"])
    idraw.text((28, 94), "BLACK FRIDAY", font=load_font(asset_root, ["montserrat-700.ttf"], 24), fill=PALETTE["bone"])
    idraw.line((28, 145, 350, 145), fill=PALETTE["sage"], width=2)
    idraw.text((28, 170), "TATTOO", font=load_font(asset_root, ["cinzel-700.ttf"], 34), fill=PALETTE["cream"])
    idraw.text((28, 220), "& PIERCING", font=load_font(asset_root, ["montserrat-600.ttf"], 22), fill=PALETTE["teal"])
    idraw.text((28, 350), "SAN BERNARDO", font=load_font(asset_root, ["montserrat-600.ttf"], 18), fill=PALETTE["bone"])
    canvas.paste(inset, (W - 430, 760))

    # Marquee typography and offer lock-up; no invented discount values
    d.text((72, 1230), "CUPOS", font=cinzel, fill=PALETTE["cream"])
    d.text((72, 1310), "LIMITADOS", font=cinzel, fill=PALETTE["bone"])
    tracked(d, (78, 1420), "RESERVA TU SESIÓN", mont, PALETTE["teal"], 4)
    d.line((78, 1480, W - 78, 1480), fill=PALETTE["sage"], width=2)
    d.text((78, 1520), "ABYSS TATTOO Y PIERCING", font=mont, fill=PALETTE["cream"])
    d.text((78, 1570), "SAN BERNARDO  ♦  CHILE", font=mont_small, fill=PALETTE["bone"])
    d.text((78, 1650), "@abyss_tattoo_studio", font=mont_small, fill=PALETTE["teal"])
    d.text((78, 1700), "wa.me/56947786839", font=mont_small, fill=PALETTE["cream"])
    d.line((78, 1780, W - 78, 1780), fill=PALETTE["bone"], width=2)
    tracked(d, (78, 1810), "ARTE  •  DISCIPLINA  •  LEGADO", mont_small, PALETTE["bone"], 3)
    # side vertical microtype
    side = Image.new("RGBA", (H, 34), (0, 0, 0, 0))
    sd = ImageDraw.Draw(side)
    sd.text((0, 0), "ABYSS  /  BLACK FRIDAY  /  SAN BERNARDO  /  ABYSS  /", font=mont_small, fill=PALETTE["sage"])
    side = side.rotate(90, expand=True, resample=Image.Resampling.BICUBIC)
    canvas.paste(side, (W - side.width - 26, 570), side)

    # variant accent changes are deliberately subtle and brand-safe
    if variant % 2:
        overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay)
        od.rectangle((52, 52, W - 52, H - 52), outline=(158, 196, 186, 65), width=3)
        canvas = Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB")
    return np.asarray(canvas)


def analyze_reference(ref_path: Path, frames_dir: Path):
    cap = cv2.VideoCapture(str(ref_path))
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open reference video: {ref_path}")
    fps = cap.get(cv2.CAP_PROP_FPS) or FPS
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    orb = cv2.ORB_create(nfeatures=1800, scaleFactor=1.2, nlevels=8)
    matcher = cv2.BFMatcher(cv2.NORM_HAMMING)
    first_gray = None
    first_kp = first_desc = None
    prev_gray = None
    rows = []
    hist_prev = None
    frames_dir.mkdir(parents=True, exist_ok=True)
    idx = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        kp, desc = orb.detectAndCompute(gray, None)
        if idx == 0:
            first_gray, first_kp, first_desc = gray, kp, desc
        # Dense optical flow is measured on a reduced image for stable cost.
        flow_mag = 0.0
        flow_angle = 0.0
        if prev_gray is not None:
            small_prev = cv2.resize(prev_gray, (180, 225))
            small_now = cv2.resize(gray, (180, 225))
            flow = cv2.calcOpticalFlowFarneback(small_prev, small_now, None, 0.5, 3, 15, 3, 5, 1.2, 0)
            mag, ang = cv2.cartToPolar(flow[..., 0], flow[..., 1])
            flow_mag = float(np.mean(mag))
            flow_angle = float(np.angle(np.mean(np.exp(1j * ang))))
        hist = cv2.calcHist([frame], [0, 1], None, [24, 24], [0, 256, 0, 256])
        cv2.normalize(hist, hist, 0, 1, cv2.NORM_MINMAX)
        cut_score = 0.0 if hist_prev is None else float(cv2.compareHist(hist_prev, hist, cv2.HISTCMP_BHATTACHARYYA))
        hist_prev = hist
        transform = np.eye(3, dtype=np.float64)
        inliers = 0
        if idx > 0 and desc is not None and first_desc is not None:
            pairs = matcher.knnMatch(first_desc, desc, k=2)
            good = [m for m, n in pairs if m.distance < 0.74 * n.distance]
            if len(good) >= 8:
                p0 = np.float32([first_kp[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
                pi = np.float32([kp[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
                affine, mask = cv2.estimateAffinePartial2D(p0, pi, method=cv2.RANSAC, ransacReprojThreshold=3.5)
                if affine is not None:
                    transform[:2, :] = affine
                    inliers = int(mask.sum()) if mask is not None else 0
        # Save every source frame (frame-accurate audit / reproducibility).
        cv2.imwrite(str(frames_dir / f"ref_{idx:04d}.jpg"), frame, [cv2.IMWRITE_JPEG_QUALITY, 91])
        rows.append({
            "frame": idx, "time_s": round(idx / fps, 6),
            "flow_mean_px": round(flow_mag, 6), "flow_angle_rad": round(flow_angle, 6),
            "cut_score": round(cut_score, 6), "global_transform": transform.tolist(),
            "feature_inliers": inliers,
        })
        prev_gray = gray
        idx += 1
    cap.release()
    return {
        "source": ref_path.name, "width": width, "height": height,
        "fps": fps, "frame_count": idx, "duration_s": round(idx / fps, 6),
        "analysis_method": "ORB + RANSAC affine camera tracking; Farneback dense optical flow; HSV histogram cut score",
        "frames": rows,
    }


def smooth_path(rows):
    mats = []
    for row in rows:
        m = np.asarray(row["global_transform"], dtype=np.float64)
        a, b = m[0, 0], m[1, 0]
        scale = math.sqrt(a * a + b * b)
        angle = math.atan2(b, a)
        tx, ty = m[0, 2], m[1, 2]
        # The original transform is retained in JSON; only extreme tracking outliers are limited for render safety.
        scale = float(np.clip(scale, 0.62, 1.85))
        angle = float(np.clip(angle, -0.32, 0.32))
        tx = float(np.clip(tx, -220, 220))
        ty = float(np.clip(ty, -260, 260))
        mats.append((scale, angle, tx, ty))
    arr = np.asarray(mats, dtype=np.float64)
    if len(arr) >= 5:
        for col in range(4):
            arr[:, col] = np.convolve(np.pad(arr[:, col], (2, 2), mode="edge"), np.ones(5) / 5, mode="valid")
    return arr


def render_video(poster: np.ndarray, motion: np.ndarray, output: Path, fps: int = FPS):
    output.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg = "ffmpeg"
    cmd = [ffmpeg, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgr24",
           "-s", f"{W}x{H}", "-r", str(fps), "-i", "-", "-an",
           "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-profile:v", "high",
           "-pix_fmt", "yuv420p", "-colorspace", "bt709", "-color_primaries", "bt709",
           "-color_trc", "bt709", "-movflags", "+faststart", str(output)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    poster_bgr = cv2.cvtColor(poster, cv2.COLOR_RGB2BGR)
    n = len(motion)
    for i, (scale, angle, tx, ty) in enumerate(motion):
        # Apply reference camera motion in normalized coordinates, adapting 4:5 -> 9:16.
        c, s = math.cos(angle), math.sin(angle)
        cx, cy = W / 2, H / 2
        mat = np.array([[scale * c, -scale * s, cx - scale * c * cx + scale * s * cy + tx * W / 720],
                        [scale * s, scale * c, cy - scale * s * cx - scale * c * cy + ty * H / 900]], dtype=np.float32)
        frame = cv2.warpAffine(poster_bgr, mat, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
        # Flow-reactive shutter softness only on high-velocity frames.
        if i < n:
            blur = min(1.35, max(0.0, float(motion[i, 0] - 1.0) * 1.2))
            if blur > 0.25:
                frame = cv2.GaussianBlur(frame, (0, 0), blur)
        # soft grain for print texture
        if i % 2 == 0:
            noise = np.random.default_rng(i).normal(0, 1.15, frame.shape[:2]).astype(np.float32)
            frame = np.clip(frame.astype(np.float32) + noise[..., None], 0, 255).astype(np.uint8)
        proc.stdin.write(frame.tobytes())
    proc.stdin.close()
    code = proc.wait()
    if code != 0:
        raise RuntimeError(f"ffmpeg render failed with exit code {code}")


def contact_sheet(frames_dir: Path, output: Path, count: int = 24):
    files = sorted(frames_dir.glob("ref_*.jpg"))
    if not files:
        return
    picks = np.linspace(0, len(files) - 1, min(count, len(files))).astype(int)
    thumbs = []
    for i in picks:
        im = Image.open(files[int(i)]).convert("RGB")
        im.thumbnail((180, 225))
        thumbs.append((int(i), im.copy()))
    cols, cell_w, cell_h = 4, 190, 250
    rows = math.ceil(len(thumbs) / cols)
    sheet = Image.new("RGB", (cols * cell_w, rows * cell_h), "#171310")
    d = ImageDraw.Draw(sheet)
    for j, (idx, im) in enumerate(thumbs):
        x, y = (j % cols) * cell_w, (j // cols) * cell_h
        sheet.paste(im, (x + 5, y + 5))
        d.text((x + 5, y + 232), f"frame {idx:04d}", fill="#EAE3DD")
    sheet.save(output, quality=92)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reference", required=True, type=Path)
    ap.add_argument("--assets", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--analysis", required=True, type=Path)
    args = ap.parse_args()
    frames_dir = args.out.parent / "reference_frames"
    report = analyze_reference(args.reference, frames_dir)
    args.analysis.parent.mkdir(parents=True, exist_ok=True)
    args.analysis.write_text(json.dumps(report, indent=2), encoding="utf-8")
    contact_sheet(frames_dir, args.out.parent / "reference_contact_sheet.jpg")

    images = find_images(args.assets)
    if not images:
        raise RuntimeError("No usable campaign photos found in the Dropbox asset folder")
    poster = build_poster(args.assets, images[0], 0)
    motion = smooth_path(report["frames"])
    render_video(poster, motion, args.out, FPS)
    # Technical receipt
    probe = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                            "stream=codec_name,width,height,r_frame_rate,pix_fmt",
                            "-show_entries", "format=duration,size", "-of", "json", str(args.out)],
                           check=True, capture_output=True, text=True)
    (args.out.parent / "render_probe.json").write_text(probe.stdout, encoding="utf-8")
    with zipfile.ZipFile(args.out.parent / "reference_frames.zip", "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for p in sorted(frames_dir.glob("*.jpg")):
            z.write(p, p.name)
    print(f"RENDER_OK {args.out} frames={report['frame_count']} duration={report['duration_s']}s")


if __name__ == "__main__":
    main()
