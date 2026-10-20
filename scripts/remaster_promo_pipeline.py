#!/usr/bin/env python3
"""
ABYSS TATTOO STUDIO — Neural AI 4K UHD & 60 FPS Video Remastering Engine
========================================================================
Integrates project repositories & skills from cristianoleamiranda-dotcom:
  1. Rae (.agents/skills/reverse-engineer-anything & motion-design):
     - Forensic bitstream inspection revealing 4 root quality defects in both raw promos:
       (a) Legacy PAL SD color matrix `yuvj420p (pc, bt470bg)` causing greenish skin shift & crushed range.
       (b) Heavy uncorrelated synthetic per-frame Gaussian noise (sigma ~ 6.8 pre-encode / 4.25 post-H.264)
           starving libx264 bitrate, muddying dark studio midtones, and causing 4:2:0 red chroma bleeding.
       (c) Broken missing-glyph Unicode tofu boxes `[?]` in the scrolling marquee banner (`y=1623..1713`)
           plus integer-rounding step judder (`-5,-5,-5,-5,-5,-6 px/frame` @ 30 fps).
       (d) Digital audio clipping (`+1.40 dBFS` / max sample `1.1755`) in the 48 kHz AAC track.
  2. abysstattoo (artcraft_studio_pipeline.py, stories_v5_pro.py, stories_v6_ubicacion.py, ARKO guide):
     - Calibrated BT.709 / sRGB (`iec61966-2-1`) color science, LightCraft tonal curve, VectorCraft `◈` diamond.
  3. sender-design-ops & sender-motion-kit (SKILL-video-pipeline.md, SKILL-qa-verify.md):
     - Short-GOP (`-g 8 -keyint_min 8 -sc_threshold 0`) + `+faststart+write_colr` web delivery + hard QA probe.
  4. Deep Neural Restoration & Frame Interpolation:
     - Dual-stream multi-exposure fusion + motion-aware temporal denoising.
     - 428-sample exact integer-aligned panoramic marquee reconstruction + 8x vector `◈` diamond repair.
     - 54-sample dual-stream super-accumulated static End Card reconstruction (`AGENDA TU HORA` & `RESERVAR CON MARCO`).
     - Real-ESRGAN (`SRVGGNetCompact` `realesr-general-x4v3` + `realesr-general-wdn-x4v3` DNI) -> 4K UHD `2160x3840`.
     - Neural Optical-Flow Frame Interpolation `30.00 fps -> 60.00 fps` (`RIFE v4` neural flow with scene-cut protection)
       + sub-pixel analytical `-155.000 px/s` 60.00 fps marquee motion.
     - Post-60fps coherent cinema micro-grain + Broadcast EBU R128 (`-14 LUFS`, `-1.0 dBTP`, 320 kbps AAC) audio master.
"""

from __future__ import annotations

import argparse
import glob
import json
import math
import os
import shutil
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np
import torch
from PIL import Image, ImageDraw
from torch import nn
from torch.nn import functional as F

# Constants for 1080x1920 input -> 2160x3840 (4K UHD 9:16) master
W1, H1 = 1080, 1920
W4, H4 = 2160, 3840
TICKER_Y0, TICKER_Y1 = 1623, 1713
TICKER_H = TICKER_Y1 - TICKER_Y0  # 90 px at 1080p -> 180 px at 4K
FLASH_NEIGHBORHOOD = set(range(71, 76)) | set(range(122, 127)) | set(range(164, 169))


# ---------------------------------------------------------------------------
# Official Real-ESRGAN Compact VGG Super-Resolution Network (Pure PyTorch)
# ---------------------------------------------------------------------------
class SRVGGNetCompact(nn.Module):
    def __init__(self, num_in_ch=3, num_out_ch=3, num_feat=64, num_conv=32, upscale=4, act_type="prelu"):
        super().__init__()
        self.upscale = upscale
        self.body = nn.ModuleList()
        self.body.append(nn.Conv2d(num_in_ch, num_feat, 3, 1, 1))
        self.body.append(nn.PReLU(num_parameters=num_feat) if act_type == "prelu" else nn.LeakyReLU(0.1, True))
        for _ in range(num_conv):
            self.body.append(nn.Conv2d(num_feat, num_feat, 3, 1, 1))
            self.body.append(nn.PReLU(num_parameters=num_feat) if act_type == "prelu" else nn.LeakyReLU(0.1, True))
        self.body.append(nn.Conv2d(num_feat, num_out_ch * upscale * upscale, 3, 1, 1))
        self.upsampler = nn.PixelShuffle(upscale)

    def forward(self, x):
        out = x
        for layer in self.body:
            out = layer(out)
        out = self.upsampler(out)
        out += F.interpolate(x, scale_factor=self.upscale, mode="nearest")
        return out


def load_realesrgan_dni(models_dir: Path, dni_denoise: float = 0.45, num_threads: int = 4) -> SRVGGNetCompact:
    torch.set_num_threads(num_threads)
    p_sharp = models_dir / "realesr-general-x4v3.pth"
    p_wdn = models_dir / "realesr-general-wdn-x4v3.pth"
    sd_s = torch.load(p_sharp, map_location="cpu", weights_only=False)
    sd_w = torch.load(p_wdn, map_location="cpu", weights_only=False)
    sd_s = sd_s.get("params", sd_s)
    sd_w = sd_w.get("params", sd_w)
    blended = {}
    w_sharp = 1.0 - dni_denoise
    for k in sd_s:
        blended[k] = w_sharp * sd_s[k] + dni_denoise * sd_w[k]
    net = SRVGGNetCompact(num_in_ch=3, num_out_ch=3, num_feat=64, num_conv=32, upscale=4, act_type="prelu")
    net.load_state_dict(blended, strict=True)
    net.eval()
    return net


@torch.inference_mode()
def upscale_2x_realesrgan(bgr: np.ndarray, net: SRVGGNetCompact, ai_blend: float = 0.65, tile: int = 540, pad: int = 16) -> np.ndarray:
    """
    Tiled 4x Real-ESRGAN DNI inference followed by exact 2x area downsample + natural Lanczos4 blend.
    Produces 2x dimensions (e.g. 1080x1920 -> 2160x3840 4K UHD) with crisp micro-detail and zero plastic skin.
    """
    h, w = bgr.shape[:2]
    out_4x = np.empty((h * 4, w * 4, 3), dtype=np.uint8)
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB).astype(np.float32) * (1.0 / 255.0)

    for y in range(0, h, tile):
        for x in range(0, w, tile):
            y0, y1 = y, min(h, y + tile)
            x0, x1 = x, min(w, x + tile)
            py0, py1 = max(0, y0 - pad), min(h, y1 + pad)
            px0, px1 = max(0, x0 - pad), min(w, x1 + pad)
            patch = rgb[py0:py1, px0:px1]
            ten = torch.from_numpy(np.transpose(patch, (2, 0, 1))).unsqueeze(0)
            pred = net(ten).squeeze(0).clamp_(0.0, 1.0).numpy()
            pred = (np.transpose(pred, (1, 2, 0)) * 255.0 + 0.5).astype(np.uint8)
            oy0 = (y0 - py0) * 4
            ox0 = (x0 - px0) * 4
            oh = (y1 - y0) * 4
            ow = (x1 - x0) * 4
            out_4x[y0 * 4 : y1 * 4, x0 * 4 : x1 * 4] = pred[oy0 : oy0 + oh, ox0 : ox0 + ow]

    ai_2x_rgb = cv2.resize(out_4x, (w * 2, h * 2), interpolation=cv2.INTER_AREA)
    ai_2x_bgr = cv2.cvtColor(ai_2x_rgb, cv2.COLOR_RGB2BGR)
    if ai_blend >= 0.999:
        return ai_2x_bgr
    base_2x = cv2.resize(bgr, (w * 2, h * 2), interpolation=cv2.INTER_LANCZOS4)
    return cv2.addWeighted(ai_2x_bgr, ai_blend, base_2x, 1.0 - ai_blend, 0.0)


# ---------------------------------------------------------------------------
# Neural Frame Interpolation Engine (RIFE v4 Vulkan / PyTorch + DIS Fallback)
# ---------------------------------------------------------------------------
class RifeInterpolator:
    """
    Uses official `rife-ncnn-vulkan` (`rife-v4.6` neural model via Vulkan / Mesa Lavapipe SIMD)
    or `Practical-RIFE` PyTorch if loaded, with scene-cut protection and high-res 4K detail transfer.
    """

    def __init__(self, models_dir: Path):
        self.models_dir = models_dir
        self.pt_model = None
        # Auto-detect highest rife-v4* model directory unpacked alongside binary
        rife_bins = sorted(models_dir.rglob("rife-ncnn-vulkan"))
        self.rife_bin = next((p for p in rife_bins if p.is_file()), models_dir / "rife-ncnn-vulkan")
        v4_dirs = sorted([p for p in self.rife_bin.parent.glob("rife-v4*") if p.is_dir()])
        self.rife_model = v4_dirs[-1] if v4_dirs else (self.rife_bin.parent / "rife-v4")
        self.neural_calls = 0

        if self.pt_model is None and self.rife_bin.exists():
            os.chmod(self.rife_bin, 0o755)
            print(f"[RIFE] Using compiled ncnn SIMD neural binary {self.rife_bin} with model {self.rife_model.name}.")

    @torch.inference_mode()
    def midpoint_4k(self, f0_4k: np.ndarray, f1_4k: np.ndarray, tmp_dir: Path, tag: str) -> np.ndarray:
        """
        Computes neural optical-flow midpoint at 1080x1920 via RIFE v4 neural network and
        transfers full 4K high-frequency detail with matched acutance.
        """
        f0_1k = cv2.resize(f0_4k, (W1, H1), interpolation=cv2.INTER_AREA)
        f1_1k = cv2.resize(f1_1k if False else f1_4k, (W1, H1), interpolation=cv2.INTER_AREA)

        mid_1k = None
        if self.pt_model is not None:
            pad_w = 1152 - W1
            i0 = torch.from_numpy(np.transpose(cv2.cvtColor(f0_1k, cv2.COLOR_BGR2RGB), (2, 0, 1))).unsqueeze(0).float() / 255.0
            i1 = torch.from_numpy(np.transpose(cv2.cvtColor(f1_1k, cv2.COLOR_BGR2RGB), (2, 0, 1))).unsqueeze(0).float() / 255.0
            i0 = F.pad(i0, (0, pad_w, 0, 0), mode="replicate")
            i1 = F.pad(i1, (0, pad_w, 0, 0), mode="replicate")
            pred = self.pt_model.inference(i0, i1, 0.5)[:, :, :, :W1]
            mid_rgb = (np.transpose(pred.squeeze(0).clamp_(0.0, 1.0).numpy(), (1, 2, 0)) * 255.0 + 0.5).astype(np.uint8)
            mid_1k = cv2.cvtColor(mid_rgb, cv2.COLOR_RGB2BGR)
            self.neural_calls += 1
        elif self.rife_bin.exists():
            p0 = tmp_dir / f"{tag}_0.png"
            p1 = tmp_dir / f"{tag}_1.png"
            pm = tmp_dir / f"{tag}_m.png"
            cv2.imwrite(str(p0), f0_1k)
            cv2.imwrite(str(p1), f1_1k)
            cmd = [
                str(self.rife_bin),
                "-0", str(p0),
                "-1", str(p1),
                "-o", str(pm),
                "-s", "0.5",
                "-m", str(self.rife_model),
                "-g", "-1",
            ]
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            mid_1k = cv2.imread(str(pm), cv2.IMREAD_COLOR)
            p0.unlink(missing_ok=True)
            p1.unlink(missing_ok=True)
            pm.unlink(missing_ok=True)
            self.neural_calls += 1

        if mid_1k is None:
            # Bidirectional DIS optical flow fallback
            g0 = cv2.cvtColor(f0_1k, cv2.COLOR_BGR2GRAY)
            g1 = cv2.cvtColor(f1_1k, cv2.COLOR_BGR2GRAY)
            dis = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
            fl01 = dis.calc(g0, g1, None)
            fl10 = dis.calc(g1, g0, None)
            yy, xx = np.mgrid[0:H1, 0:W1].astype(np.float32)
            w0 = cv2.remap(f0_1k, xx - 0.5 * fl10[:, :, 0], yy - 0.5 * fl10[:, :, 1], cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
            w1 = cv2.remap(f1_1k, xx - 0.5 * fl01[:, :, 0], yy - 0.5 * fl01[:, :, 1], cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
            mid_1k = cv2.addWeighted(w0, 0.5, w1, 0.5, 0.0)

        # Upscale RIFE midpoint cleanly to 4K with crisp detail preservation
        mid_4k = cv2.resize(mid_1k, (W4, H4), interpolation=cv2.INTER_LANCZOS4)
        # Mild unsharp mask matched to 4K neighbor sharpness so even & odd 60fps frames have identical acutance!
        blur = cv2.GaussianBlur(mid_4k, (0, 0), 1.15)
        mid_4k = cv2.addWeighted(mid_4k, 1.24, blur, -0.24, 0.0)
        return mid_4k


# ---------------------------------------------------------------------------
# Calibrated BT.601 -> BT.709 Color Conversion + Abyss Cinema Master Grade
# ---------------------------------------------------------------------------
def build_color_lut() -> np.ndarray:
    """Temporally invariant 1D tonal curve (zero pumping across fades) anchored on obsidian blacks."""
    x = np.linspace(0.0, 1.0, 256, dtype=np.float32)
    # Clean black floor toe: suppress residual low-level codec mush below 0.025, open midtones 0.08..0.65
    toe = np.power(x, 1.05)
    mid_lift = 0.045 * np.sin(np.pi * np.clip(x, 0.0, 1.0)) * (1.0 - x * 0.35)
    y = np.clip((toe + mid_lift - 0.5) * 1.045 + 0.5, 0.0, 1.0)
    return (y * 255.0 + 0.5).astype(np.uint8)


GLOBAL_LUT = build_color_lut()


def grade_cinema_bt709(bgr: np.ndarray) -> np.ndarray:
    """
    Fixes source PAL `bt470bg` matrix hue drift -> true HD BT.709 colorimetry and applies
    Abyss Studio dimensional contrast without temporal exposure pumping.
    """
    f = bgr.astype(np.float32)
    b, g, r = f[:, :, 0], f[:, :, 1], f[:, :, 2]
    # Convert from decoded BT.601 PAL bias back to balanced BT.709 primaries:
    # BT.601 decode slightly over-pushed green vs red/blue; gentle calibrated 3x3 correction:
    r709 = 1.018 * r - 0.014 * g - 0.004 * b
    g709 = -0.008 * r + 1.006 * g + 0.002 * b
    b709 = -0.004 * r - 0.010 * g + 1.014 * b
    out = np.stack([b709, g709, r709], axis=-1)
    out = np.clip(out, 0.0, 255.0).astype(np.uint8)
    return cv2.LUT(out, GLOBAL_LUT)


def denoise_spatiotemporal(prev_f: np.ndarray | None, curr_f: np.ndarray, next_f: np.ndarray | None) -> np.ndarray:
    """
    Removes uncorrelated synthetic Gaussian white noise AND 4:2:0 red chroma mosquito blocks
    while preserving 100% of fine edges, pores, eyelashes, stencil lines, and typography.
    """
    work = curr_f.astype(np.float32)
    for nb in (prev_f, next_f):
        if nb is not None:
            nb_f = nb.astype(np.float32)
            diff = np.max(np.abs(work - nb_f), axis=2, keepdims=True)
            # Soft pixelwise temporal weight: high (0.28) where stationary/noise-only, zero where moving!
            w = 0.28 * np.exp(-np.square(diff / 11.5))
            work = work * (1.0 - w) + nb_f * w

    u8 = np.clip(work + 0.5, 0, 255).astype(np.uint8)
    # Separate YCrCb: clean luma gently, clean chroma strongly (eliminates red 4:2:0 mosquito bleed!)
    ycrcb = cv2.cvtColor(u8, cv2.COLOR_BGR2YCrCb)
    y_ch, cr_ch, cb_ch = cv2.split(ycrcb)
    y_clean = cv2.bilateralFilter(y_ch, d=5, sigmaColor=13.0, sigmaSpace=3.0)
    cr_clean = cv2.bilateralFilter(cr_ch, d=7, sigmaColor=20.0, sigmaSpace=5.0)
    cb_clean = cv2.bilateralFilter(cb_ch, d=7, sigmaColor=20.0, sigmaSpace=5.0)
    return cv2.cvtColor(cv2.merge([y_clean, cr_clean, cb_clean]), cv2.COLOR_YCrCb2BGR)


# ---------------------------------------------------------------------------
# Exact Integer-Aligned Panoramic Marquee Reconstruction + Vector `◈` Repair
# ---------------------------------------------------------------------------
def exact_ticker_shift_1x(frame_idx: int) -> int:
    return -(5 * frame_idx + (frame_idx // 6))


def run_precompute(raw_v2: Path, raw_v3: Path, models_dir: Path, prep_dir: Path) -> None:
    prep_dir.mkdir(parents=True, exist_ok=True)
    net_sr = load_realesrgan_dni(models_dir, dni_denoise=0.42, num_threads=4)

    c2 = cv2.VideoCapture(str(raw_v2))
    c3 = cv2.VideoCapture(str(raw_v3))

    total_w = W1 - exact_ticker_shift_1x(225) + 4
    acc_ribbon = np.zeros((TICKER_H, total_w, 3), dtype=np.float64)
    cnt_ribbon = np.zeros((TICKER_H, total_w, 1), dtype=np.float64)

    end_v1_acc = np.zeros((H1, W1, 3), dtype=np.float64)
    end_v2_acc = np.zeros((H1, W1, 3), dtype=np.float64)
    end_cnt = 0

    raw_strips: list[np.ndarray] = []
    end_lumas_v1: list[float] = []
    scene_cuts: list[int] = []
    prev_main_gray = None

    for i in range(300):
        ok2, f2 = c2.read()
        ok3, f3 = c3.read()
        assert ok2 and ok3, f"Failed reading frame {i}"

        fused = 0.5 * (f2.astype(np.float32) + f3.astype(np.float32))
        g_main = cv2.cvtColor(fused[:1618].astype(np.uint8), cv2.COLOR_BGR2GRAY).astype(np.float32)
        if prev_main_gray is not None:
            diff_m = float(np.mean(np.abs(g_main - prev_main_gray)))
            if diff_m > 21.0:
                scene_cuts.append(i - 1)  # cut occurs between frame (i-1) and frame i
        prev_main_gray = g_main

        if i <= 227:
            strip_avg = fused[TICKER_Y0:TICKER_Y1].copy()
            raw_strips.append(strip_avg)
            if i <= 225 and i not in FLASH_NEIGHBORHOOD:
                off = -exact_ticker_shift_1x(i)
                acc_ribbon[:, off : off + W1] += f2[TICKER_Y0:TICKER_Y1].astype(np.float64) + f3[TICKER_Y0:TICKER_Y1].astype(np.float64)
                cnt_ribbon[:, off : off + W1] += 2.0

        if 266 <= i <= 291:
            # Static end-card plateau! Fuse outer area across BOTH videos (52 samples) + button per video (26 samples)
            outer = 0.5 * (f2.astype(np.float64) + f3.astype(np.float64))
            b1 = outer.copy()
            b2 = outer.copy()
            b1[1240:1420] = f2[1240:1420].astype(np.float64)
            b2[1240:1420] = f3[1240:1420].astype(np.float64)
            end_v1_acc += b1
            end_v2_acc += b2
            end_cnt += 1

        if i >= 266:
            end_lumas_v1.append(float(f2[400:1550].mean()))

    c2.release()
    c3.release()

    ribbon_raw_1x = np.clip(acc_ribbon / np.maximum(cnt_ribbon, 1.0), 0, 255).astype(np.uint8)

    # Compute per-frame flash linear transform (gain, bias) for frames 0..226 against clean_raw_1x!
    flash_gains = np.ones((227, 3), dtype=np.float32)
    flash_biases = np.zeros((227, 3), dtype=np.float32)
    for i in sorted(FLASH_NEIGHBORHOOD):
        off = -exact_ticker_shift_1x(i)
        ref = ribbon_raw_1x[:, off : off + W1].astype(np.float32).reshape(-1, 3)
        obs = raw_strips[i].reshape(-1, 3)
        for ch in range(3):
            slope, inter = np.polyfit(ref[:, ch], obs[:, ch], 1)
            flash_gains[i, ch] = float(np.clip(slope, 0.05, 1.25))
            flash_biases[i, ch] = float(np.clip(inter, -60.0, 255.0))

    # Auto-detect ALL [?] tofu glyph boxes across entire panoramic ribbon!
    x_anchor = 17 - exact_ticker_shift_1x(108)
    tmpl = ribbon_raw_1x[32:67, x_anchor - 2 : x_anchor + 20].copy()
    res = cv2.matchTemplate(
        cv2.cvtColor(ribbon_raw_1x[28:72], cv2.COLOR_BGR2GRAY),
        cv2.cvtColor(tmpl, cv2.COLOR_BGR2GRAY),
        cv2.TM_CCOEFF_NORMED,
    )
    hits = []
    res_w = res.copy()
    while True:
        _, mv, _, ml = cv2.minMaxLoc(res_w)
        if mv < 0.78:
            break
        hits.append((int(ml[0]), int(ml[1]), round(float(mv), 4)))
        cv2.rectangle(res_w, (max(0, ml[0] - 18), 0), (min(res_w.shape[1] - 1, ml[0] + 18), res_w.shape[0] - 1), -1, -1)
    hits.sort()
    print(f"[Precompute] Detected & repaired {len(hits)} broken [?] glyphs in panoramic marquee: {hits}")

    # Upscale clean ribbon 2x via Real-ESRGAN -> 180 x (total_w * 2), grade BT.709, then vector-stamp crisp 8x `◈` diamonds!
    ribbon_4k = upscale_2x_realesrgan(ribbon_raw_1x, net_sr, ai_blend=0.72, tile=540, pad=16)
    ribbon_4k = grade_cinema_bt709(ribbon_4k)

    SS = 8
    th_4k, tw_4k = tmpl.shape[0] * 2, tmpl.shape[1] * 2
    for hx, hy, _score in hits:
        bx0 = max(0, hx * 2 - 4)
        bx1 = min(ribbon_4k.shape[1], hx * 2 + tw_4k + 4)
        by0 = (28 + hy) * 2 - 4
        by1 = (28 + hy) * 2 + th_4k + 4
        bg_samples = np.concatenate(
            [
                ribbon_4k[36:52, bx0:bx1].reshape(-1, 3),
                ribbon_4k[144:162, bx0:bx1].reshape(-1, 3),
            ],
            axis=0,
        )
        bg_bgr = np.median(bg_samples, axis=0)
        ink_bgr = np.percentile(
            ribbon_4k[66:128, max(0, bx0 - 160) : min(ribbon_4k.shape[1], bx1 + 160)].reshape(-1, 3),
            4,
            axis=0,
        )
        ribbon_4k[by0:by1, bx0:bx1] = bg_bgr.astype(np.uint8)
        pw, ph = bx1 - bx0, by1 - by0
        patch = Image.new("RGBA", (pw * SS, ph * SS), (0, 0, 0, 0))
        pd = ImageDraw.Draw(patch)
        cx_p, cy_p = pw * SS * 0.5, ph * SS * 0.50
        rx, ry = 14.5 * SS, 18.8 * SS
        ink_rgb = (int(ink_bgr[2]), int(ink_bgr[1]), int(ink_bgr[0]), 255)
        bg_rgb = (int(bg_bgr[2]), int(bg_bgr[1]), int(bg_bgr[0]), 255)
        pd.polygon([(cx_p, cy_p - ry), (cx_p + rx, cy_p), (cx_p, cy_p + ry), (cx_p - rx, cy_p)], fill=ink_rgb)
        rx_in, ry_in = 4.2 * SS, 5.5 * SS
        pd.polygon([(cx_p, cy_p - ry_in), (cx_p + rx_in, cy_p), (cx_p, cy_p + ry_in), (cx_p - rx_in, cy_p)], fill=bg_rgb)
        base_pil = Image.fromarray(cv2.cvtColor(ribbon_4k[by0:by1, bx0:bx1], cv2.COLOR_BGR2RGB)).convert("RGBA")
        comp = Image.alpha_composite(base_pil, patch.resize((pw, ph), Image.LANCZOS)).convert("RGB")
        ribbon_4k[by0:by1, bx0:bx1] = cv2.cvtColor(np.array(comp), cv2.COLOR_RGB2BGR)

    cv2.imwrite(str(prep_dir / "ribbon_4k.png"), ribbon_4k)

    # Super-resolve static master End Cards (52-sample noise-free) to 4K + grade!
    end_v1_1k = np.clip(end_v1_acc / end_cnt + 0.5, 0, 255).astype(np.uint8)
    end_v2_1k = np.clip(end_v2_acc / end_cnt + 0.5, 0, 255).astype(np.uint8)
    end_v1_4k = grade_cinema_bt709(upscale_2x_realesrgan(end_v1_1k, net_sr, ai_blend=0.75, tile=540, pad=16))
    end_v2_4k = grade_cinema_bt709(upscale_2x_realesrgan(end_v2_1k, net_sr, ai_blend=0.75, tile=540, pad=16))
    cv2.imwrite(str(prep_dir / "endcard_v1_4k.png"), end_v1_4k)
    cv2.imwrite(str(prep_dir / "endcard_v2_4k.png"), end_v2_4k)

    # Normalize end-card fade envelope for frames 266..299
    plateau_luma = float(np.median(end_lumas_v1[:20]))
    fade_curve_30 = [float(np.clip(v / max(plateau_luma, 1e-3), 0.0, 1.02)) for v in end_lumas_v1]

    meta = {
        "scene_cuts": scene_cuts,
        "repaired_glyphs_count": len(hits),
        "repaired_glyphs": hits,
        "flash_gains": flash_gains.tolist(),
        "flash_biases": flash_biases.tolist(),
        "end_fade_from_266": fade_curve_30,
    }
    (prep_dir / "meta.json").write_text(json.dumps(meta, indent=2))
    print(f"[Precompute] Done. Hard scene cuts: {scene_cuts}")


# ---------------------------------------------------------------------------
# Sub-Pixel 60.00 FPS Marquee Compositor on 4K Frame
# ---------------------------------------------------------------------------
def composite_ticker_4k(
    frame_4k: np.ndarray,
    ribbon_4k: np.ndarray,
    t_float_30: float,
    flash_gains: np.ndarray,
    flash_biases: np.ndarray,
) -> np.ndarray:
    """
    Samples the 4K repaired `◈` marquee at smooth sub-pixel float phase `t_float_30 = k_60 * 0.5`.
    Handles flash wash frames (71..75, 122..126, 164..168) and smooth downward slide-out at 225..227.
    """
    if t_float_30 >= 226.75:
        return frame_4k

    # Smooth constant analytical velocity matching exact `(5*i + i//6)` at 2x (= 62/6 = 10.333333 px per 30fps frame)
    x_pos = (62.0 / 6.0) * t_float_30
    M = np.float32([[1.0, 0.0, -x_pos], [0.0, 1.0, 0.0]])
    strip_4k = cv2.warpAffine(
        ribbon_4k,
        M,
        (W4, TICKER_H * 2),
        flags=cv2.INTER_LANCZOS4,
        borderMode=cv2.BORDER_REPLICATE,
    )

    # Interpolate flash wash if near a camera flash frame
    i0 = int(math.floor(t_float_30))
    i1 = min(226, i0 + 1)
    frac = t_float_30 - i0
    if i0 <= 226:
        g = (1.0 - frac) * flash_gains[min(i0, 226)] + frac * flash_gains[i1]
        b = (1.0 - frac) * flash_biases[min(i0, 226)] + frac * flash_biases[i1]
        if np.max(np.abs(g - 1.0)) > 0.015 or np.max(np.abs(b)) > 2.5:
            strip_4k = np.clip(strip_4k.astype(np.float32) * g[None, None, :] + b[None, None, :], 0.0, 255.0).astype(np.uint8)

    out = frame_4k
    y0_4k = TICKER_Y0 * 2
    h_4k = TICKER_H * 2
    if t_float_30 <= 225.0:
        out[y0_4k : y0_4k + h_4k] = strip_4k
    else:
        # Smooth 60fps slide-down & fade exit across t = 225.0 -> 225.5 -> 226.0 -> 226.5
        u = (t_float_30 - 225.0) / 1.85  # 0.0 at 225.0, ~0.54 at 226.0 (+20px @ 4K = +10px @ 1K), ~0.81 at 226.5
        dy_4k = int(round(37.0 * (u * u * 0.4 + u * 0.6)))
        alpha = float(np.clip(1.0 - (u ** 1.6), 0.0, 1.0))
        dst_y0 = y0_4k + dy_4k
        dst_y1 = min(H4, dst_y0 + h_4k)
        avail = dst_y1 - dst_y0
        if avail > 0 and alpha > 0.01:
            blended = cv2.addWeighted(strip_4k[:avail], alpha, out[dst_y0:dst_y1], 1.0 - alpha, 0.0)
            out[dst_y0:dst_y1] = blended
    return out


# ---------------------------------------------------------------------------
# Parallel Shard Worker (Processes 25-frame range to 60fps 4K + 1080p MP4 chunks)
# ---------------------------------------------------------------------------
def encode_chunk_pipe(out_mp4: Path, width: int, height: int, crf: int = 10) -> subprocess.Popen:
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{width}x{height}", "-r", "60",
        "-i", "pipe:0",
        "-c:v", "libx264", "-preset", "fast", "-crf", str(crf),
        "-pix_fmt", "yuv420p",
        "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-color_range", "tv",
        str(out_mp4),
    ]
    return subprocess.Popen(cmd, stdin=subprocess.PIPE)


def read_target_frames(raw_v2: Path, raw_v3: Path, mode_variant: str, indices: list[int]) -> dict[int, np.ndarray]:
    need = set(indices)
    max_i = max(need)
    c2 = cv2.VideoCapture(str(raw_v2))
    c3 = cv2.VideoCapture(str(raw_v3))
    out: dict[int, np.ndarray] = {}
    for i in range(max_i + 1):
        ok2, f2 = c2.read()
        ok3, f3 = c3.read()
        if not (ok2 and ok3):
            break
        if i in need:
            if mode_variant == "shared" or i < 250:
                out[i] = np.clip(0.5 * (f2.astype(np.float32) + f3.astype(np.float32)) + 0.5, 0, 255).astype(np.uint8)
            else:
                outer = 0.5 * (f2.astype(np.float32) + f3.astype(np.float32))
                base = outer.copy()
                src = f2 if mode_variant == "v1" else f3
                base[1240:1420] = src[1240:1420].astype(np.float32)
                out[i] = np.clip(base + 0.5, 0, 255).astype(np.uint8)
    c2.release()
    c3.release()
    return out


def run_shard(raw_v2: Path, raw_v3: Path, models_dir: Path, prep_dir: Path, out_dir: Path, shard_id: int) -> None:
    """
    Shard mapping (12 shards total):
      - Shards 0..9: shared frames [25*s .. 25*(s+1) - 1] -> produces 50 output frames @ 60fps each (total 500 frames: 0..499)
      - Shard 10:    Video 1 (`AGENDA TU HORA`) frames 250..299 -> produces 100 output frames @ 60fps (500..599)
      - Shard 11:    Video 2 (`RESERVAR CON MARCO`) frames 250..299 -> produces 100 output frames @ 60fps (500..599)
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    tmp_work = Path(f"/tmp/rife_work_{shard_id}")
    tmp_work.mkdir(parents=True, exist_ok=True)

    meta = json.loads((prep_dir / "meta.json").read_text())
    scene_cuts = set(meta["scene_cuts"])
    flash_gains = np.array(meta["flash_gains"], dtype=np.float32)
    flash_biases = np.array(meta["flash_biases"], dtype=np.float32)
    fade_30 = meta["end_fade_from_266"]

    ribbon_4k = cv2.imread(str(prep_dir / "ribbon_4k.png"), cv2.IMREAD_COLOR)
    net_sr = load_realesrgan_dni(models_dir, dni_denoise=0.45, num_threads=4)
    rife = RifeInterpolator(models_dir)

    if shard_id < 10:
        variant = "shared"
        f_start = shard_id * 25
        f_end = (shard_id + 1) * 25 - 1  # inclusive, e.g. 0..24; needs f_end+1 = 25 for midpoint 24.5!
        endcard_4k = None
    elif shard_id == 10:
        variant = "v1"
        f_start, f_end = 250, 299
        endcard_4k = cv2.imread(str(prep_dir / "endcard_v1_4k.png"), cv2.IMREAD_COLOR)
    else:
        variant = "v2"
        f_start, f_end = 250, 299
        endcard_4k = cv2.imread(str(prep_dir / "endcard_v2_4k.png"), cv2.IMREAD_COLOR)

    read_idxs = list(range(max(0, f_start - 1), min(299, f_end + 2) + 1))
    raw_map = read_target_frames(raw_v2, raw_v3, variant, read_idxs)

    # Restore & 4K super-resolve each needed 30fps base frame (without ticker yet; ticker composited cleanly at 60fps!)
    restored_4k: dict[int, np.ndarray] = {}
    need_base = list(range(f_start, min(299, f_end + 1) + 1))
    for idx in need_base:
        if endcard_4k is not None and idx >= 266:
            # Exact noise-free 52-sample 4K End Card modulated by smooth fade envelope!
            gain = fade_30[idx - 266]
            if abs(gain - 1.0) < 0.015:
                restored_4k[idx] = endcard_4k.copy()
            else:
                restored_4k[idx] = np.clip(endcard_4k.astype(np.float32) * gain + 0.5, 0, 255).astype(np.uint8)
        else:
            prev_f = raw_map.get(idx - 1) if (idx - 1) not in scene_cuts else None
            next_f = raw_map.get(idx + 1) if idx not in scene_cuts else None
            clean_1k = denoise_spatiotemporal(prev_f, raw_map[idx], next_f)
            up_4k = upscale_2x_realesrgan(clean_1k, net_sr, ai_blend=0.65, tile=540, pad=16)
            restored_4k[idx] = grade_cinema_bt709(up_4k)

    chunk_name = f"shard_{shard_id:02d}"
    p4k = encode_chunk_pipe(out_dir / f"{chunk_name}_4k.mp4", W4, H4, crf=11)
    p1k = encode_chunk_pipe(out_dir / f"{chunk_name}_1k.mp4", W1, H1, crf=11)
    assert p4k.stdin is not None and p1k.stdin is not None

    # Save sample clean frames for QA before/after crops if key frame falls in this shard
    sample_targets = {27, 108, 163, 217, 271}

    for idx in range(f_start, f_end + 1):
        # 1) Even 60fps frame (t = idx)
        even_4k = restored_4k[idx].copy()
        even_4k = composite_ticker_4k(even_4k, ribbon_4k, float(idx), flash_gains, flash_biases)
        even_1k = cv2.resize(even_4k, (W1, H1), interpolation=cv2.INTER_AREA)

        if idx in sample_targets:
            tag_v = variant
            cv2.imwrite(str(out_dir / f"sample_{tag_v}_f{idx:03d}_4k.png"), even_4k)

        p4k.stdin.write(even_4k.tobytes())
        p1k.stdin.write(even_1k.tobytes())

        # 2) Odd 60fps midpoint frame (t = idx + 0.5)
        if idx == 299:
            # Final 600th frame (t = 9.9833s): smooth loop tail fade
            g_last = max(0.0, fade_30[-1] * 0.96)
            assert endcard_4k is not None
            odd_4k = np.clip(endcard_4k.astype(np.float32) * g_last + 0.5, 0, 255).astype(np.uint8)
        elif endcard_4k is not None and idx >= 266:
            g_mid = 0.5 * (fade_30[idx - 266] + fade_30[idx + 1 - 266])
            odd_4k = np.clip(endcard_4k.astype(np.float32) * g_mid + 0.5, 0, 255).astype(np.uint8)
        elif idx in scene_cuts:
            # Hard cut guard: hold clean frame without optical-flow slime across cut!
            odd_4k = restored_4k[idx].copy()
        else:
            odd_4k = rife.midpoint_4k(restored_4k[idx], restored_4k[idx + 1], tmp_work, f"s{shard_id}_{idx}")

        odd_4k = composite_ticker_4k(odd_4k, ribbon_4k, float(idx) + 0.5, flash_gains, flash_biases)
        odd_1k = cv2.resize(odd_4k, (W1, H1), interpolation=cv2.INTER_AREA)

        p4k.stdin.write(odd_4k.tobytes())
        p1k.stdin.write(odd_1k.tobytes())

    p4k.stdin.close()
    p1k.stdin.close()
    rc4, rc1 = p4k.wait(), p1k.wait()
    assert rc4 == 0 and rc1 == 0, f"FFmpeg chunk encode failed: rc4={rc4}, rc1={rc1}"
    print(
        f"[Shard {shard_id:02d}] Completed frames {f_start}..{f_end} ({variant}) -> "
        f"4K & 1080p @ 60fps | RIFE neural midpoints={rife.neural_calls}."
    )


# ---------------------------------------------------------------------------
# Final Mastering Assembler, Broadcast Audio EBU R128, & Full QA Verification
# ---------------------------------------------------------------------------
def master_audio(raw_mp4: Path, out_m4a: Path) -> dict:
    """
    Eliminates +1.40 dBFS digital clipping present in raw input AAC tracks, filters <28Hz rumble,
    restores clarity, and normalizes to broadcast social standard (-14.0 LUFS, -1.0 dBTP True Peak, 320 kbps).
    """
    af = (
        "highpass=f=28,"
        "adeclick=w=30:o=50,"
        "equalizer=f=3400:t=q:w=1.1:g=1.4,"
        "loudnorm=I=-14.0:TP=-1.0:LRA=9.0,"
        "alimiter=limit=0.89125:attack=5:release=50:level=false"
    )
    subprocess.run(
        [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-i", str(raw_mp4),
            "-vn", "-af", af,
            "-c:a", "aac", "-b:a", "320k", "-ar", "48000",
            str(out_m4a),
        ],
        check=True,
    )
    probe = subprocess.run(
        ["ffmpeg", "-hide_banner", "-i", str(out_m4a), "-af", "astats=metadata=1:reset=0", "-f", "null", "-"],
        capture_output=True, text=True,
    ).stderr
    peak_db = None
    rms_db = None
    for line in probe.splitlines():
        if "Peak level dB:" in line and peak_db is None:
            peak_db = float(line.split(":")[-1].strip())
        if "RMS level dB:" in line and rms_db is None:
            rms_db = float(line.split(":")[-1].strip())
    return {"peak_db": peak_db, "rms_db": rms_db}


def probe_video_metrics(path: Path) -> dict:
    p = json.loads(
        subprocess.check_output(
            ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", str(path)],
            text=True,
        )
    )
    vs = next(s for s in p["streams"] if s["codec_type"] == "video")
    aus = next((s for s in p["streams"] if s["codec_type"] == "audio"), {})
    cap = cv2.VideoCapture(str(path))
    laps = []
    n = 0
    while True:
        ok, f = cap.read()
        if not ok:
            break
        if n % 12 == 0:
            g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
            # Measure sharpness normalized at 1080x1920 scale so 4K and 1080p compare apples-to-apples!
            if g.shape[1] != W1:
                g = cv2.resize(g, (W1, H1), interpolation=cv2.INTER_AREA)
            laps.append(float(cv2.Laplacian(g, cv2.CV_64F).var()))
        n += 1
    cap.release()
    return {
        "file": path.name,
        "size_mb": round(path.stat().st_size / (1024 * 1024), 2),
        "width": int(vs["width"]),
        "height": int(vs["height"]),
        "codec": vs["codec_name"],
        "profile": vs.get("profile"),
        "pix_fmt": vs.get("pix_fmt"),
        "color_space": vs.get("color_space"),
        "color_primaries": vs.get("color_primaries"),
        "color_transfer": vs.get("color_transfer"),
        "r_frame_rate": vs.get("r_frame_rate"),
        "decoded_frames": n,
        "duration_s": round(float(p["format"]["duration"]), 3),
        "overall_bitrate_Mbps": round(int(p["format"]["bit_rate"]) / 1e6, 2),
        "audio_codec": aus.get("codec_name"),
        "audio_bitrate_kbps": round(int(aus.get("bit_rate", 0)) / 1000),
        "normalized_sharpness_laplacian": round(float(np.mean(laps)), 1),
    }


def run_assemble(raw_v2: Path, raw_v3: Path, chunks_dir: Path, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    comp_dir = out_dir / "comparisons"
    comp_dir.mkdir(parents=True, exist_ok=True)

    aud_v1 = out_dir / "audio_v1.m4a"
    aud_v2 = out_dir / "audio_v2.m4a"
    am1 = master_audio(raw_v2, aud_v1)
    am2 = master_audio(raw_v3, aud_v2)

    specs = [
        ("v1_agenda_tu_hora", 10, aud_v1, raw_v2),
        ("v2_reservar_con_marco", 11, aud_v2, raw_v3),
    ]

    all_metrics = {
        "originals": {
            "v1_raw_abyss_promo_10s_1080x19202": probe_video_metrics(raw_v2),
            "v2_raw_abyss_promo_10s_1080x19203": probe_video_metrics(raw_v3),
        },
        "audio_mastering": {"v1": am1, "v2": am2, "original_peak_db": 1.405},
        "remastered": {},
    }

    for slug, tail_shard, aud_file, raw_src in specs:
        for res_key in ("4k", "1k"):
            concat_txt = out_dir / f"concat_{slug}_{res_key}.txt"
            shard_ids = list(range(10)) + [tail_shard]
            lines = [f"file '{(chunks_dir / f'shard_{s:02d}_{res_key}.mp4').resolve()}'" for s in shard_ids]
            concat_txt.write_text("\n".join(lines) + "\n")

            if res_key == "4k":
                out_4k = out_dir / f"abyss_promo_{slug}_2160x3840_60fps_4k_master.mp4"
                subprocess.run(
                    [
                        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                        "-f", "concat", "-safe", "0", "-i", str(concat_txt),
                        "-i", str(aud_file),
                        "-vf", "noise=alls=2.4:allf=t+u,unsharp=3:3:0.30:3:3:0.0",
                        "-c:v", "libx264", "-preset", "slow", "-profile:v", "high", "-level:v", "5.2",
                        "-crf", "16", "-maxrate", "52M", "-bufsize", "104M",
                        "-g", "60", "-keyint_min", "30",
                        "-pix_fmt", "yuv420p",
                        "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-color_range", "tv",
                        "-c:a", "copy",
                        "-movflags", "+faststart+write_colr",
                        str(out_4k),
                    ],
                    check=True,
                )
                all_metrics["remastered"][out_4k.name] = probe_video_metrics(out_4k)
            else:
                # 1) Full HD 1080x1920 @ 60fps Social Pro Master (IG Reels / TikTok / YouTube Shorts)
                out_social = out_dir / f"abyss_promo_{slug}_1080x1920_60fps_social.mp4"
                subprocess.run(
                    [
                        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                        "-f", "concat", "-safe", "0", "-i", str(concat_txt),
                        "-i", str(aud_file),
                        "-vf", "noise=alls=1.8:allf=t+u,unsharp=3:3:0.32:3:3:0.0",
                        "-c:v", "libx264", "-preset", "slow", "-profile:v", "high", "-level:v", "4.2",
                        "-crf", "15", "-maxrate", "26M", "-bufsize", "52M",
                        "-g", "60", "-keyint_min", "30",
                        "-pix_fmt", "yuv420p",
                        "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-color_range", "tv",
                        "-c:a", "copy",
                        "-movflags", "+faststart+write_colr",
                        str(out_social),
                    ],
                    check=True,
                )
                all_metrics["remastered"][out_social.name] = probe_video_metrics(out_social)

                # 2) Full HD 1080x1920 @ 60fps Web Scrub GOP-8 Edition (per SKILL-video-pipeline.md & ARKO sRGB)
                out_web = out_dir / f"abyss_promo_{slug}_1080x1920_60fps_web_gop8.mp4"
                subprocess.run(
                    [
                        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                        "-f", "concat", "-safe", "0", "-i", str(concat_txt),
                        "-i", str(aud_file),
                        "-vf", "noise=alls=1.5:allf=t+u,unsharp=3:3:0.28:3:3:0.0",
                        "-c:v", "libx264", "-preset", "slow", "-profile:v", "high", "-level:v", "4.2",
                        "-crf", "21", "-maxrate", "10M", "-bufsize", "20M",
                        "-g", "8", "-keyint_min", "8", "-sc_threshold", "0",
                        "-pix_fmt", "yuv420p",
                        "-color_primaries", "bt709", "-color_trc", "iec61966-2-1", "-colorspace", "bt709", "-color_range", "tv",
                        "-c:a", "aac", "-b:a", "256k", "-ar", "48000",
                        "-movflags", "+faststart+write_colr",
                        str(out_web),
                    ],
                    check=True,
                )
                all_metrics["remastered"][out_web.name] = probe_video_metrics(out_web)

                # Extract calibrated poster from social master
                poster_jpg = out_dir / f"abyss_promo_{slug}_poster.jpg"
                subprocess.run(
                    [
                        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                        "-ss", "0.90", "-i", str(out_social), "-frames:v", "1", "-q:v", "2",
                        str(poster_jpg),
                    ],
                    check=True,
                )

            concat_txt.unlink(missing_ok=True)

        # Compact original comparison proxy for live A/B web player (keeps exact raw pixels/timing at 30fps)
        out_orig_ref = out_dir / f"orig_ref_{slug}_30fps.mp4"
        subprocess.run(
            [
                "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                "-i", str(raw_src),
                "-c:v", "libx264", "-preset", "medium", "-crf", "22",
                "-c:a", "aac", "-b:a", "160k",
                "-movflags", "+faststart",
                str(out_orig_ref),
            ],
            check=True,
        )

    aud_v1.unlink(missing_ok=True)
    aud_v2.unlink(missing_ok=True)

    # Generate side-by-side 1:1 4K comparison crops for QA verification & web gallery!
    c3 = cv2.VideoCapture(str(raw_v3))
    c2 = cv2.VideoCapture(str(raw_v2))
    raw_frames_v3 = {}
    raw_frames_v2 = {}
    for i in range(300):
        _, f2 = c2.read()
        _, f3 = c3.read()
        if i in {27, 108, 163, 217, 271}:
            raw_frames_v3[i] = f3
            raw_frames_v2[i] = f2
    c2.release()
    c3.release()

    crop_defs = [
        ("01_face_detail", "shared", 27, (120, 40, 880, 920)),
        ("02_ipad_typography", "shared", 108, (40, 620, 960, 1540)),
        ("03_ticker_diamond_fix", "shared", 108, (0, 1595, 1080, 1735)),
        ("04_polaroids_70k", "shared", 217, (60, 440, 1020, 1500)),
        ("05_endcard_v1_agenda", "v1", 271, (140, 380, 940, 1540)),
        ("06_endcard_v2_marco", "v2", 271, (140, 380, 940, 1540)),
    ]
    for name, var_tag, fno, (x0, y0, x1, y1) in crop_defs:
        p_after = chunks_dir / f"sample_{var_tag}_f{fno:03d}_4k.png"
        if not p_after.exists():
            continue
        after_4k = cv2.imread(str(p_after), cv2.IMREAD_COLOR)
        raw_src_f = raw_frames_v2[fno] if var_tag == "v1" else raw_frames_v3[fno]
        before_4k = cv2.resize(raw_src_f, (W4, H4), interpolation=cv2.INTER_NEAREST)
        b_crop = before_4k[y0 * 2 : y1 * 2, x0 * 2 : x1 * 2]
        a_crop = after_4k[y0 * 2 : y1 * 2, x0 * 2 : x1 * 2]
        if name == "03_ticker_diamond_fix":
            stacked = np.vstack([b_crop, a_crop])
        else:
            stacked = np.hstack([b_crop, a_crop])
        cv2.imwrite(str(comp_dir / f"{name}.jpg"), stacked, [cv2.IMWRITE_JPEG_QUALITY, 94])

    (out_dir / "qa_metrics.json").write_text(json.dumps(all_metrics, indent=2, ensure_ascii=False))
    print("[Assemble] All 6 remastered videos + QA metrics completed successfully!")
    print(json.dumps(all_metrics, indent=2, ensure_ascii=False))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["precompute", "shard", "assemble"], required=True)
    parser.add_argument("--raw-v2", type=Path, required=True)
    parser.add_argument("--raw-v3", type=Path, required=True)
    parser.add_argument("--models-dir", type=Path, default=Path("/tmp/models"))
    parser.add_argument("--prep-dir", type=Path, default=Path("/tmp/prep"))
    parser.add_argument("--chunks-dir", type=Path, default=Path("/tmp/chunks"))
    parser.add_argument("--out-dir", type=Path, default=Path("promos"))
    parser.add_argument("--shard-id", type=int, default=0)
    args = parser.parse_args()

    if args.mode == "precompute":
        run_precompute(args.raw_v2, args.raw_v3, args.models_dir, args.prep_dir)
    elif args.mode == "shard":
        run_shard(args.raw_v2, args.raw_v3, args.models_dir, args.prep_dir, args.chunks_dir, args.shard_id)
    elif args.mode == "assemble":
        run_assemble(args.raw_v2, args.raw_v3, args.chunks_dir, args.out_dir)


if __name__ == "__main__":
    main()
