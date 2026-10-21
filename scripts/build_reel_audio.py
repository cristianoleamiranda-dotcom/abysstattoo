#!/usr/bin/env python3
"""
build_reel_audio.py — Diseño sonoro del Reel Comercial de 15 s de Abyss Tattoo Studio.

1. Cama musical: se reutiliza la pista del comercial anterior (100 BPM) empalmada en un grid
   de negras exacto (7.20 s = 12 beats, loop de 4.80 s = 8 beats) para que ningún corte
   quede fuera de pulso, y se corta en seco a los 12.6 s para dejar respirar el CTA.
2. Foley sintetizado: impactos, whooshes de transición, riser, clicks de obturador y ping de
   confirmación, todos ubicados en los cortes reales de la línea de tiempo.
3. Master: compresión suave, fundido de cola y normalización de pico para entrega social.
"""

import os

import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, lfilter, sosfilt

ROOT = "/home/user/abysstattoo"
SR = 48000
DUR = 15.0
SRC = os.path.join(ROOT, "dropbox/abyss_promo_v1_agenda_tu_hora_1080x1920_60fps_social.mp4")
WAV_IN = "/tmp/reel_music_src.wav"
OUT = os.path.join(ROOT, "film/reel_abyss_15s_audio.wav")

rng = np.random.default_rng(20251021)


# ------------------------------------------------------------------ utilidades
def bp(x, lo, hi, order=2):
    sos = butter(order, [lo / (SR / 2), hi / (SR / 2)], btype="band", output="sos")
    return sosfilt(sos, x)


def lp(x, f, order=2):
    sos = butter(order, f / (SR / 2), btype="low", output="sos")
    return sosfilt(sos, x)


def hp(x, f, order=2):
    sos = butter(order, f / (SR / 2), btype="high", output="sos")
    return sosfilt(sos, x)


def env(n, attack, decay, curve=2.0):
    a = int(attack * SR)
    d = max(1, n - a)
    e = np.concatenate([np.linspace(0, 1, max(1, a)) ** 0.6, np.linspace(1, 0, d) ** curve])
    return e[:n]


def add(buf, sig, at, gain=1.0, pan=0.0):
    i = int(at * SR)
    n = min(len(sig), buf.shape[0] - i)
    if n <= 0:
        return
    l = np.cos((pan + 1) * np.pi / 4)
    r = np.sin((pan + 1) * np.pi / 4)
    buf[i:i + n, 0] += sig[:n] * gain * l
    buf[i:i + n, 1] += sig[:n] * gain * r


def whoosh(dur=0.5, f_lo=260, f_hi=3800, curve=1.6):
    n = int(dur * SR)
    noise = rng.normal(0, 1, n)
    out = np.zeros(n)
    blocks = 24
    seg = n // blocks
    for b in range(blocks):
        p = b / (blocks - 1)
        lo = f_lo + (f_hi - f_lo) * p * 0.55
        hi = lo * 2.2
        band = bp(noise[max(0, (b - 1) * seg):(b + 2) * seg], min(lo, 4000), min(hi, 16000))
        c = band[seg:2 * seg] if len(band) >= 2 * seg else band[:seg]
        out[b * seg:b * seg + len(c)] = c[:seg]
    e = np.concatenate([np.linspace(0, 1, int(n * 0.55)) ** 2, np.linspace(1, 0, n - int(n * 0.55)) ** curve])
    return out * e


def impact(dur=0.62, f0=96, f1=38, punch=1.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    sweep = np.sin(2 * np.pi * (f1 * t + (f0 - f1) * (1 - np.exp(-t * 13)) / 13))
    body = sweep * np.exp(-t * 5.6)
    click = hp(rng.normal(0, 1, n), 1600) * np.exp(-t * 55) * 0.5
    sub = lp(rng.normal(0, 1, n), 120) * np.exp(-t * 8) * 0.45
    return (body * punch + click + sub) * 0.55


def riser(dur=1.25, f0=180, f1=1400):
    n = int(dur * SR)
    t = np.arange(n) / SR
    tone = np.sin(2 * np.pi * (f0 * (f1 / f0) ** (t / dur)) * t) * np.linspace(0.05, 0.5, n)
    noise = hp(rng.normal(0, 1, n), 900) * np.linspace(0.02, 0.35, n) ** 1.5
    e = np.linspace(0, 1, n) ** 2.2
    return (tone + noise) * e


def ping(dur=0.9, f=1180):
    n = int(dur * SR)
    t = np.arange(n) / SR
    a = np.sin(2 * np.pi * f * t) * np.exp(-t * 7)
    b = np.sin(2 * np.pi * f * 1.5 * t) * np.exp(-t * 11) * 0.5
    c = np.sin(2 * np.pi * f * 2.02 * t) * np.exp(-t * 17) * 0.25
    return (a + b + c) * 0.4


def tick(dur=0.06, f=2400):
    n = int(dur * SR)
    t = np.arange(n) / SR
    return (hp(rng.normal(0, 1, n), 1800) * np.exp(-t * 90) * 0.5 + np.sin(2 * np.pi * f * t) * np.exp(-t * 60) * 0.3)


def boom(dur=1.5, f=52):
    n = int(dur * SR)
    t = np.arange(n) / SR
    return np.sin(2 * np.pi * (f * (1 - 0.12 * t / dur)) * t) * np.exp(-t * 2.4) * 0.55


# ------------------------------------------------------------------ música
def music_bed():
    import subprocess
    subprocess.run([f"{ROOT}/.venv/bin/ffmpeg", "-y", "-i", SRC, "-vn", "-ac", "2", "-ar", str(SR), WAV_IN],
                   check=True, stderr=subprocess.DEVNULL)
    sr, x = wavfile.read(WAV_IN)
    x = x.astype(np.float32) / 32768.0
    if x.shape[1] == 1:
        x = np.repeat(x, 2, axis=1)
    x = hp(x.T, 26).T  # limpia retumbe bajo
    x = x / (np.abs(x).max() + 1e-9) * 0.9

    def cut(a, b):
        return x[int(a * SR):int(b * SR)]

    def xfade(a, b, ms=22):
        n = int(ms * SR / 1000)
        a = a.copy()
        a[-n:] = a[-n:] * np.linspace(1, 0, n)[:, None] + b[:n] * np.linspace(0, 1, n)[:, None]
        return np.concatenate([a[:-n], b], axis=0)

    body = cut(0.00, 7.20)            # 12 negras
    loop = cut(2.40, 7.20)            # 8 negras
    m = xfade(body, loop)
    m = xfade(m, loop)
    m = m[: int(12.60 * SR)]
    return m


def build():
    total = int(DUR * SR)
    music = music_bed()
    bed = np.zeros((total, 2), np.float32)
    n = min(len(music), total)
    bed[:n] = music[:n]
    # fade musical para entregar el CTA en seco pero elegante
    f0, f1 = int(11.95 * SR), int(12.62 * SR)
    bed[f0:f1] *= np.linspace(1, 0, f1 - f0)[:, None] ** 0.7
    bed[f1:] = 0
    # pequeño sidechain en cada corte fuerte para que el foley respire
    for at, depth in [(1.20, 0.55), (6.60, 0.65), (9.00, 0.6), (10.20, 0.5)]:
        i = int(at * SR)
        seg = int(0.22 * SR)
        bed[i:i + seg] *= np.linspace(depth, 1, seg)[:, None]

    fx = np.zeros((total, 2), np.float32)

    add(fx, impact(0.70, 104, 40, 1.15), 0.00, 0.85)          # apertura
    add(fx, whoosh(0.55, 220, 5200, 1.4), 1.02, 0.30, -0.25)  # entrada al hook 2
    add(fx, impact(0.55, 92, 36, 0.9), 1.20, 0.62)
    add(fx, tick(), 1.22, 0.5, 0.3)
    add(fx, whoosh(0.60, 200, 4600, 1.6), 2.18, 0.34, 0.3)    # whip a fachada
    add(fx, whoosh(0.42, 300, 6200, 1.5), 4.06, 0.26, -0.3)   # travelling pasillo
    add(fx, tick(), 5.42, 0.32, 0.25)
    add(fx, whoosh(0.34, 500, 7200, 1.6), 6.46, 0.24, 0.35)   # macro
    add(fx, impact(0.48, 88, 44, 0.55), 6.60, 0.42)
    add(fx, whoosh(0.62, 180, 5000, 1.5), 7.62, 0.36, -0.35)  # whip portafolio
    add(fx, tick(), 7.84, 0.30, 0.2)
    add(fx, impact(0.42, 96, 48, 0.5), 9.00, 0.40)
    add(fx, whoosh(0.40, 260, 6800, 1.5), 10.04, 0.30, 0.3)   # split piercing
    add(fx, whoosh(0.55, 200, 4400, 1.5), 11.24, 0.32, -0.2)  # a equipo
    add(fx, riser(1.20), 11.42, 0.34)                         # build al cierre
    add(fx, impact(0.95, 108, 34, 1.25), 12.60, 1.00)         # hit del cierre
    add(fx, boom(1.7), 12.60, 0.55)                           # cola baja
    add(fx, ping(1.0, 1240), 13.30, 0.42, 0.15)               # aparición del CTA
    add(fx, tick(0.05, 2800), 12.86, 0.5, -0.2)               # pop del emblema
    add(fx, tick(0.05, 2100), 13.72, 0.30, 0.25)

    mix = bed * 0.72 + fx * 0.78

    # master: compresión suave + limitador
    mix = np.tanh(mix * 1.25) * 0.92
    peak = np.abs(mix).max()
    mix = mix / peak * 0.90
    # fundido final
    tail = int(0.25 * SR)
    mix[-tail:] *= np.linspace(1, 0, tail)[:, None] ** 1.5
    # dithering suave
    mix += rng.normal(0, 1e-5, mix.shape).astype(np.float32)
    wavfile.write(OUT, SR, (np.clip(mix, -1, 1) * 32767).astype(np.int16))
    rms = np.sqrt((mix ** 2).mean())
    print(f"Audio listo: {OUT}  dur={len(mix)/SR:.2f}s  peak={np.abs(mix).max():.3f}  rms={rms:.4f}")


if __name__ == "__main__":
    build()
