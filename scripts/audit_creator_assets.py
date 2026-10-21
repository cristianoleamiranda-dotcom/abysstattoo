#!/usr/bin/env python3
"""Metadata-only media gate for CapCut creator deliverables (FFmpeg required).

Example: python3 scripts/audit_creator_assets.py --profile creator-vertical file1.mp4 file2.mp4
Visual/community-policy, ownership, editability, and music-rights review remains manual.
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path


def ffmpeg_path() -> str | None:
    found = shutil.which("ffmpeg")
    if found:
        return found
    try:
        import imageio_ffmpeg  # type: ignore
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def probe(ffmpeg: str, file: Path) -> dict[str, object]:
    # Decode the first video frame to distinguish valid inputs from truncated/corrupt files.
    result = subprocess.run(
        [ffmpeg, "-hide_banner", "-v", "info", "-i", str(file), "-map", "0:v:0", "-frames:v", "1", "-f", "null", "-"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False,
    )
    text = result.stderr
    duration_match = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", text)
    stream_lines = [line for line in text.splitlines() if "Stream #" in line]
    video_line = next((line for line in stream_lines if ": Video:" in line), "")
    video_match = re.search(r"(\d{2,5})x(\d{2,5}).*?(\d+(?:\.\d+)?)\s+fps", video_line)
    audio = any(": Audio:" in line for line in stream_lines)
    if result.returncode != 0 or not duration_match or not video_match:
        raise ValueError((text[-1200:] or f"ffmpeg exited {result.returncode}").strip())
    h, m, s = duration_match.groups()
    duration = int(h) * 3600 + int(m) * 60 + float(s)
    return {
        "duration": duration,
        "width": int(video_match.group(1)),
        "height": int(video_match.group(2)),
        "fps": float(video_match.group(3)),
        "audio": audio,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=("metadata", "creator-vertical"), default="metadata")
    parser.add_argument("files", nargs="+", type=Path)
    args = parser.parse_args()
    ffmpeg = ffmpeg_path()
    if not ffmpeg:
        print("ERROR: ffmpeg not found. Install FFmpeg or imageio-ffmpeg.", file=sys.stderr)
        return 2

    failed = False
    for file in args.files:
        try:
            data = probe(ffmpeg, file)
            checks = []
            if args.profile == "creator-vertical":
                checks = [
                    (data["width"] == 1080 and data["height"] == 1920, "1080x1920 vertical canvas"),
                    (12.0 <= data["duration"] <= 20.0, "duration 12–20 s"),
                    (abs(data["fps"] - 60.0) < 0.02, "60 fps"),
                    (data["audio"], "audio stream present"),
                ]
            bad = [name for ok, name in checks if not ok]
            status = "FAIL" if bad else "PASS"
            failed |= bool(bad)
            print(
                f"{status} {file}: {data['width']}x{data['height']} "
                f"{data['fps']:.3f} fps, {data['duration']:.2f}s, "
                f"audio={'yes' if data['audio'] else 'no'}"
                + (f" | failed: {', '.join(bad)}" if bad else "")
            )
        except (OSError, ValueError) as exc:
            failed = True
            print(f"FAIL {file}: {exc}")
    print("NOTE: metadata gate only; perform visual safety, rights, text/editability and CapCut-review checks manually.")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
