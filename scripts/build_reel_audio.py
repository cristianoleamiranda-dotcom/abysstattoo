#!/usr/bin/env python3
"""
build_reel_audio.py — Diseño sonoro publicitario 48 kHz estéreo para el Reel Comercial de 15 s.

Capas sincronizadas a grilla exacta de 100 BPM (1 negra = 0.60 s = 36 frames @ 60 fps):
 1. Cama musical oficial del estudio re-editada a grilla matemática de negras (0.00 -> 12.60 s)
    con ducking dinámico (sidechain) en cada cambio de plano principal.
 2. Foley orgánico de estudio: zumbido armónico sutil de máquina rotativa en los planos macro
    (0.00–1.20 s y 6.60–7.80 s) + ráfaga aérea atmosférica en el vuelo FPV de dron (2.40–3.60 s).
 3. Acentos cinematográficos: whooshes direccionales estéreo en los tiros de cámara, obturadores
    en los cortes rápidos del portafolio, riser de tensión (11.40–12.60 s), impacto sub-grave en
    el cierre (12.60 s) y campana cristalina de confirmación al encenderse el CTA de WhatsApp.
"""

import os
import shutil
import subprocess

import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt

ROOT = "/home/user/abysstattoo"
SR = 48000
DUR = 15.0
SRC = os.path.join(ROOT, "dropbox/abyss_promo_v1_agenda_tu_hora_1080x1920_60fps_social.mp4")
WAV_IN = "/tmp/reel_music_src.wav"
OUT = os.path.join(ROOT, "film/reel_abyss_15s_audio.wav")

rng = np.random.default_rng(20261021)


def resolve_ffmpeg() -> str:
    local_venv = os.path.join(ROOT, ".venv/bin/ffmpeg")
    if os.path.exists(local_venv):
        return local_venv
    sys_ff = shutil.which("ffmpeg")
    if sys_ff:
        return sys_ff
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def bp(x, lo, hi, order=2):
    sos = butter(order, [lo / (SR / 2), hi / (SR / 2)], btype="band", output="sos")
    return sosfilt(sos, x)


def lp(x, f, order=2):
    sos = butter(order, f / (SR / 2), btype="low", output="sos")
    return sosfilt(sos, x)


def hp(x, f, order=2):
    sos = butter(order, f / (SR / 2), btype="high", output="sos")
    return sosfilt(sos, x)


def add(buf, sig, at, gain=1.0, pan=0.0):
    i = max(0, int(round(at * SR)))
    n = min(len(sig), buf.shape[0] - i)
    if n <= 0:
        return
    l = np.cos((pan + 1.0) * np.pi / 4.0)
    r = np.sin((pan + 1.0) * np.pi / 4.0)
    buf[i : i + n, 0] += sig[:n] * gain * l
    buf[i : i + n, 1] += sig[:n] * gain * r


def whoosh(dur=0.46, f_lo=240, f_hi=4200, curve=1.5):
    n = int(dur * SR)
    noise = rng.normal(0, 1, n)
    out = np.zeros(n)
    blocks = 24
    seg = max(1, n // blocks)
    for b in range(blocks):
        p = b / (blocks - 1)
        lo = f_lo + (f_hi - f_lo) * p * 0.55
        hi = min(lo * 2.2, 16500)
        band = bp(noise[max(0, (b - 1) * seg) : (b + 2) * seg], min(lo, 4200), hi)
        c = band[seg : 2 * seg] if len(band) >= 2 * seg else band[:seg]
        out[b * seg : b * seg + len(c)] = c[:seg]
    split = int(n * 0.55)
    e = np.concatenate([np.linspace(0, 1, split) ** 2.0, np.linspace(1, 0, n - split) ** curve])
    return out * e


def drone_wind(dur=1.20):
    """Textura aerodinámica de picada FPV sobre San Bernardo."""
    n = int(dur * SR)
    noise = rng.normal(0, 1, n)
    lo_air = bp(noise, 140, 780) * 0.55
    hi_air = bp(noise, 900, 3400) * np.linspace(0.2, 1.0, n) * 0.35
    env = np.sin(np.linspace(0, np.pi, n)) ** 0.75
    return (lo_air + hi_air) * env


def rotary_tattoo_hum(dur=1.10, base_hz=116.0):
    """ Textura sutil y realista de máquina rotativa de tatuaje en macro de aguja."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    vib = 1.0 + 0.008 * np.sin(2 * np.pi * 6.5 * t)
    h1 = np.sin(2 * np.pi * base_hz * vib * t) * 0.35
    h2 = np.sin(2 * np.pi * base_hz * 2.0 * vib * t) * 0.28
    h3 = np.sin(2 * np.pi * base_hz * 3.0 * vib * t) * 0.16
    buzz = bp(rng.normal(0, 1, n), 1800, 5200) * 0.09
    fade = min(int(0.14 * SR), n // 4)
    env = np.ones(n)
    env[:fade] = np.linspace(0, 1, fade)
    env[-fade:] = np.linspace(1, 0, fade)
    return (h1 + h2 + h3 + buzz) * env


def impact(dur=0.62, f0=98, f1=36, punch=1.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    sweep = np.sin(2 * np.pi * (f1 * t + (f0 - f1) * (1 - np.exp(-t * 13)) / 13))
    body = sweep * np.exp(-t * 5.4)
    click = hp(rng.normal(0, 1, n), 1600) * np.exp(-t * 55) * 0.45
    sub = lp(rng.normal(0, 1, n), 115) * np.exp(-t * 8) * 0.45
    return (body * punch + click + sub) * 0.55


def riser(dur=1.20, f0=180, f1=1480):
    n = int(dur * SR)
    t = np.arange(n) / SR
    tone = np.sin(2 * np.pi * (f0 * (f1 / f0) ** (t / dur)) * t) * np.linspace(0.05, 0.48, n)
    noise = hp(rng.normal(0, 1, n), 950) * (np.linspace(0.02, 0.34, n) ** 1.5)
    e = np.linspace(0, 1, n) ** 2.1
    return (tone + noise) * e


def ping(dur=0.95, f=1240):
    n = int(dur * SR)
    t = np.arange(n) / SR
    a = np.sin(2 * np.pi * f * t) * np.exp(-t * 6.8)
    b = np.sin(2 * np.pi * f * 1.5 * t) * np.exp(-t * 10.5) * 0.48
    c = np.sin(2 * np.pi * f * 2.01 * t) * np.exp(-t * 16.0) * 0.24
    return (a + b + c) * 0.40


def shutter_tick(dur=0.055, f=2500):
    n = int(dur * SR)
    t = np.arange(n) / SR
    return hp(rng.normal(0, 1, n), 1900) * np.exp(-t * 95) * 0.48 + np.sin(2 * np.pi * f * t) * np.exp(-t * 65) * 0.28


def boom(dur=1.6, f=50):
    n = int(dur * SR)
    t = np.arange(n) / SR
    return np.sin(2 * np.pi * (f * (1 - 0.12 * t / dur)) * t) * np.exp(-t * 2.3) * 0.56


def music_bed():
    ff = resolve_ffmpeg()
    subprocess.run(
        [ff, "-y", "-i", SRC, "-vn", "-ac", "2", "-ar", str(SR), WAV_IN],
        check=True,
        stderr=subprocess.DEVNULL,
    )
    _, x = wavfile.read(WAV_IN)
    x = x.astype(np.float32) / 32768.0
    if x.ndim == 1:
        x = np.stack([x, x], axis=1)
    elif x.shape[1] == 1:
        x = np.repeat(x, 2, axis=1)
    x = hp(x.T, 28).T
    x = x / (np.abs(x).max() + 1e-9) * 0.90

    def cut(a, b):
        return x[int(a * SR) : int(b * SR)]

    def xfade(a, b, ms=24):
        n = int(ms * SR / 1000)
        a = a.copy()
        a[-n:] = a[-n:] * np.linspace(1, 0, n)[:, None] + b[:n] * np.linspace(0, 1, n)[:, None]
        return np.concatenate([a[:-n], b[n:]], axis=0)

    body = cut(0.00, 7.20)  # 12 negras exactas @ 100 BPM
    loop = cut(2.40, 7.20)  # 8 negras exactas @ 100 BPM
    m = xfade(body, loop)
    m = xfade(m, loop)
    return m[: int(12.62 * SR)]


def build():
    total = int(DUR * SR)
    music = music_bed()
    bed = np.zeros((total, 2), np.float32)
    bed[: len(music)] = music

    # Corte dramático del beat musical al entrar al Packshot CTA (t = 12.60 s)
    f0, f1 = int(12.00 * SR), int(12.60 * SR)
    bed[f0:f1] *= np.linspace(1.0, 0.0, f1 - f0)[:, None] ** 0.75
    bed[f1:] = 0.0

    # Sidechain ducking en los golpes clave de la línea de tiempo
    for at, depth in [(1.20, 0.55), (2.40, 0.58), (6.60, 0.62), (7.80, 0.60), (10.20, 0.56)]:
        i = int(at * SR)
        seg = int(0.22 * SR)
        bed[i : i + seg] *= np.linspace(depth, 1.0, seg)[:, None]

    fx = np.zeros((total, 2), np.float32)

    # Bloque 1: Hook (0.00 - 2.40 s)
    add(fx, impact(0.70, 106, 38, 1.15), 0.00, 0.85)
    add(fx, rotary_tattoo_hum(1.12, 118.0), 0.05, 0.22, -0.1)
    add(fx, whoosh(0.45, 220, 5200, 1.4), 1.02, 0.34, -0.30)
    add(fx, impact(0.55, 92, 36, 0.92), 1.20, 0.65)
    add(fx, shutter_tick(), 1.21, 0.45, 0.25)

    # Bloque 2: Dron FPV + Fachada 528 + Travelling POV (2.40 - 5.40 s)
    add(fx, whoosh(0.52, 180, 4800, 1.5), 2.22, 0.38, 0.30)
    add(fx, drone_wind(1.20), 2.40, 0.26, 0.0)
    add(fx, whoosh(0.38, 300, 5600, 1.5), 3.46, 0.28, -0.25)
    add(fx, shutter_tick(), 3.60, 0.34, -0.20)
    add(fx, whoosh(0.40, 260, 6200, 1.5), 4.36, 0.30, 0.28)

    # Bloque 3: Cabina Seremi + Ink Wipe Reveal (5.40 - 7.80 s)
    add(fx, shutter_tick(), 5.40, 0.34, 0.20)
    add(fx, whoosh(0.36, 420, 6800, 1.6), 6.44, 0.28, -0.32)
    add(fx, impact(0.46, 88, 42, 0.58), 6.60, 0.44)
    add(fx, rotary_tattoo_hum(0.95, 112.0), 6.62, 0.16, 0.12)

    # Bloque 4: Montaje rápido Portafolio + Titanio ASTM F136 (7.80 - 11.40 s)
    add(fx, whoosh(0.50, 180, 5400, 1.5), 7.64, 0.36, 0.35)
    add(fx, shutter_tick(), 7.80, 0.42, 0.20)
    add(fx, shutter_tick(0.05, 2900), 8.40, 0.44, -0.25)   # match-cut zoom-out 08b
    add(fx, impact(0.42, 96, 46, 0.52), 9.00, 0.42)
    add(fx, shutter_tick(0.05, 2700), 9.60, 0.42, 0.25)    # whip color 09b
    add(fx, whoosh(0.42, 260, 6800, 1.5), 10.04, 0.32, -0.30)

    # Bloque 5: Equipo + Riser -> Drop Packshot CTA (11.40 - 15.00 s)
    add(fx, whoosh(0.48, 200, 4400, 1.5), 11.24, 0.32, 0.20)
    add(fx, riser(1.18), 11.42, 0.36)
    add(fx, impact(0.95, 108, 34, 1.25), 12.60, 0.98)
    add(fx, boom(1.75), 12.60, 0.56)
    add(fx, shutter_tick(0.05, 2800), 12.78, 0.45, -0.18)
    add(fx, ping(1.05, 1245), 13.22, 0.44, 0.14)           # pop + shimmer del CTA WhatsApp

    mix = bed * 0.72 + fx * 0.78
    mix = np.tanh(mix * 1.24) * 0.92
    mix = mix / (np.abs(mix).max() + 1e-9) * 0.89

    tail = int(0.24 * SR)
    mix[-tail:] *= np.linspace(1.0, 0.0, tail)[:, None] ** 1.5
    mix += rng.normal(0.0, 1e-5, mix.shape).astype(np.float32)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    wavfile.write(OUT, SR, (np.clip(mix, -1.0, 1.0) * 32767).astype(np.int16))
    rms_db = 20.0 * np.log10(np.sqrt((mix ** 2).mean()) + 1e-9)
    print(f"Audio masterizado: {OUT} ({DUR:.2f}s @ {SR}Hz, RMS={rms_db:.1f} dBFS)")


if __name__ == "__main__":
    build()
