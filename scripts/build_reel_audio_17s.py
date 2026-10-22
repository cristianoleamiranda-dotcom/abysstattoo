#!/usr/bin/env python3
"""
build_reel_audio_17s.py — Diseño sonoro publicitario 48 kHz estéreo para el Reel
Motion Design 3D de 17 s de Abyss Tattoo Studio (José Joaquín Pérez 528, San Bernardo).

A diferencia de build_reel_audio.py (15 s, dependía de una cama musical externa en
dropbox/), esta mezcla es 100 % autocontenida y reproducible desde el repositorio:
beat publicitario sintetizado a 100 BPM exactos (1 negra = 0.60 s), foley de máquina
rotativa en los macros de aguja, whooshes/obturadores sincronizados a los cortes de
la escaleta 17 s (0.00 / 1.60 / 2.90 / 4.20 / 5.40 / 6.60 / 8.30 / 10.00 / 12.80),
riser hacia el packshot y cierre limpio (pad + boom + campana) bajo el CTA final.
"""

import os

import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SR = 48000
DUR = 17.0
BEAT = 0.60  # 100 BPM
OUT = os.path.join(ROOT, "film/reel_abyss_17s_audio.wav")

rng = np.random.default_rng(20261022)


# ---------------------------------------------------------------- filtros
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


# ---------------------------------------------------------------- síntesis musical (100 BPM · La menor)
def kick(dur=0.30):
    n = int(dur * SR)
    t = np.arange(n) / SR
    sweep = np.sin(2 * np.pi * (42.0 * t + (118.0 - 42.0) * (1 - np.exp(-t * 26)) / 26))
    body = sweep * np.exp(-t * 11.0)
    click = hp(rng.normal(0, 1, n), 2400) * np.exp(-t * 90) * 0.30
    return (body + click) * 0.95


def clap(dur=0.22):
    n = int(dur * SR)
    t = np.arange(n) / SR
    noise = bp(rng.normal(0, 1, n), 950, 3800)
    bursts = np.exp(-t * 34) + 0.7 * np.exp(-np.abs(t - 0.018) * 60) + 0.5 * np.exp(-np.abs(t - 0.037) * 55)
    tail = np.exp(-t * 14) * 0.45
    return noise * np.minimum(bursts + tail, 1.4) * 0.42


def hat(dur=0.06, open_hat=False):
    n = int(dur * SR)
    t = np.arange(n) / SR
    dec = 26.0 if open_hat else 95.0
    return hp(rng.normal(0, 1, n), 7200) * np.exp(-t * dec) * 0.20


def bass_note(freq, dur=0.27):
    n = int(dur * SR)
    t = np.arange(n) / SR
    tone = np.sin(2 * np.pi * freq * t) * 0.82 + np.sin(2 * np.pi * freq * 2 * t) * 0.22
    env = (1 - np.exp(-t * 70)) * np.exp(-t * 5.2)
    return lp(tone * env, 520) * 0.62


def pluck(freq, dur=0.34):
    n = int(dur * SR)
    t = np.arange(n) / SR
    tone = (
        np.sin(2 * np.pi * freq * t) * 0.55
        + np.sin(2 * np.pi * freq * 2 * t) * 0.24
        + np.sin(2 * np.pi * freq * 3.01 * t) * 0.10
    )
    return bp(tone * np.exp(-t * 7.5), 320, 5200) * 0.30


def pad(freqs, dur, gain=0.16):
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for f in freqs:
        out += np.sin(2 * np.pi * f * t) + 0.4 * np.sin(2 * np.pi * f * 1.005 * t)
    env = np.sin(np.linspace(0, np.pi, n)) ** 0.6
    return lp(out / max(1, len(freqs)), 1150) * env * gain


CHORDS = [  # (raíz bajo Hz, pad, arpegio) — Am · F · Dm · E
    (55.00, [220.0, 261.63, 329.63], [440.0, 523.25, 659.25, 523.25]),
    (43.65, [174.61, 220.0, 261.63], [349.23, 440.0, 523.25, 440.0]),
    (73.42, [146.83, 174.61, 220.0], [293.66, 349.23, 440.0, 349.23]),
    (41.20, [164.81, 246.94, 329.63], [329.63, 493.88, 659.25, 493.88]),
]


def music_bed():
    total = int(DUR * SR)
    bed = np.zeros((total, 2), np.float32)
    bar = BEAT * 4  # 2.40 s por compás

    t = 0.0
    bar_i = 0
    while t < 12.80:  # el beat vive hasta la entrada del packshot CTA
        root, pad_f, arp_f = CHORDS[bar_i % len(CHORDS)]
        add(bed, pad(pad_f, bar + 0.25, 0.13), t, 1.0)
        for b in range(4):
            bt = t + b * BEAT
            if bt >= 12.80:
                break
            add(bed, kick(), bt, 0.92)
            if b in (1, 3):
                add(bed, clap(), bt, 0.85)
            # bajo en corcheas con pulso publicitario
            for e in range(2):
                et = bt + e * (BEAT / 2)
                if et < 12.80:
                    add(bed, bass_note(root, 0.26), et, 0.90 if e == 0 else 0.62)
            # arpegio cristalino en corcheas, paneo alternado sutil
            for e in range(2):
                et = bt + e * (BEAT / 2)
                if et < 12.80:
                    add(bed, pluck(arp_f[(b * 2 + e) % len(arp_f)]), et, 0.55, -0.18 if e == 0 else 0.18)
            add(bed, hat(0.10, open_hat=True), bt + BEAT / 2, 0.55)
            add(bed, hat(), bt + BEAT * 0.25, 0.35)
            add(bed, hat(), bt + BEAT * 0.75, 0.35)
        t += bar
        bar_i += 1

    # Bombeo sidechain suave en cada negra (respiración publicitaria)
    env = np.ones(total, np.float32)
    bt = 0.0
    while bt < 12.80:
        i = int(bt * SR)
        seg = int(0.16 * SR)
        env[i : i + seg] *= np.linspace(0.78, 1.0, seg)
        bt += BEAT
    # Ducking marcado en los cortes de la escaleta
    for at, depth in [(1.60, 0.55), (4.20, 0.58), (6.60, 0.60), (8.30, 0.60), (10.00, 0.56)]:
        i = int(at * SR)
        seg = int(0.22 * SR)
        env[i : i + seg] *= np.linspace(depth, 1.0, seg)
    # Salida del beat: caída breve antes del impacto del CTA (12.80)
    f0, f1 = int(12.45 * SR), int(12.80 * SR)
    env[f0:f1] *= np.linspace(1.0, 0.0, f1 - f0) ** 0.8
    env[f1:] = 0.0
    return bed * env[:, None]


# ---------------------------------------------------------------- foley / acentos (reutiliza el lenguaje del 15 s)
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


def rotary_tattoo_hum(dur=1.10, base_hz=116.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    vib = 1.0 + 0.008 * np.sin(2 * np.pi * 6.5 * t)
    h = (
        np.sin(2 * np.pi * base_hz * vib * t) * 0.35
        + np.sin(2 * np.pi * base_hz * 2.0 * vib * t) * 0.28
        + np.sin(2 * np.pi * base_hz * 3.0 * vib * t) * 0.16
    )
    buzz = bp(rng.normal(0, 1, n), 1800, 5200) * 0.09
    fade = min(int(0.14 * SR), n // 4)
    env = np.ones(n)
    env[:fade] = np.linspace(0, 1, fade)
    env[-fade:] = np.linspace(1, 0, fade)
    return (h + buzz) * env


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
    return (tone + noise) * (np.linspace(0, 1, n) ** 2.1)


def ping(dur=0.95, f=1240):
    n = int(dur * SR)
    t = np.arange(n) / SR
    return (
        np.sin(2 * np.pi * f * t) * np.exp(-t * 6.8)
        + np.sin(2 * np.pi * f * 1.5 * t) * np.exp(-t * 10.5) * 0.48
        + np.sin(2 * np.pi * f * 2.01 * t) * np.exp(-t * 16.0) * 0.24
    ) * 0.40


def shutter_tick(dur=0.055, f=2500):
    n = int(dur * SR)
    t = np.arange(n) / SR
    return hp(rng.normal(0, 1, n), 1900) * np.exp(-t * 95) * 0.48 + np.sin(2 * np.pi * f * t) * np.exp(-t * 65) * 0.28


def boom(dur=1.6, f=50):
    n = int(dur * SR)
    t = np.arange(n) / SR
    return np.sin(2 * np.pi * (f * (1 - 0.12 * t / dur)) * t) * np.exp(-t * 2.3) * 0.56


def build():
    total = int(DUR * SR)
    bed = music_bed()
    fx = np.zeros((total, 2), np.float32)

    # S1 Hook macro (0.00–1.60): impacto de entrada + máquina rotativa
    add(fx, impact(0.70, 106, 38, 1.15), 0.00, 0.85)
    add(fx, rotary_tattoo_hum(1.42, 118.0), 0.05, 0.20, -0.1)

    # S2 Piezas únicas (1.60–4.20): whip al corte + whip interno 2.90
    add(fx, whoosh(0.42, 220, 5200, 1.4), 1.42, 0.34, -0.30)
    add(fx, impact(0.50, 92, 36, 0.85), 1.60, 0.58)
    add(fx, shutter_tick(), 1.61, 0.42, 0.22)
    add(fx, whoosh(0.36, 300, 5600, 1.5), 2.74, 0.28, 0.28)
    add(fx, shutter_tick(0.05, 2800), 2.90, 0.40, -0.20)

    # S3 Estudio 528 (4.20–6.60): llegada a fachada + corte interno 5.40 a vitrina
    add(fx, whoosh(0.48, 180, 4800, 1.5), 4.02, 0.36, 0.25)
    add(fx, impact(0.48, 88, 36, 0.70), 4.20, 0.50)
    add(fx, whoosh(0.34, 340, 6000, 1.5), 5.26, 0.26, -0.25)
    add(fx, shutter_tick(), 5.40, 0.34, 0.18)

    # S4 Proceso (6.60–10.00): entrada técnica + ink-wipe 8.30 + foley de máquina
    add(fx, whoosh(0.40, 260, 6200, 1.5), 6.44, 0.30, 0.28)
    add(fx, impact(0.46, 88, 42, 0.58), 6.60, 0.44)
    add(fx, rotary_tattoo_hum(1.45, 112.0), 6.66, 0.15, 0.10)
    add(fx, whoosh(0.44, 200, 5400, 1.5), 8.10, 0.32, -0.30)
    add(fx, shutter_tick(0.05, 2600), 8.30, 0.38, 0.20)
    add(fx, rotary_tattoo_hum(1.30, 114.0), 8.38, 0.13, -0.08)

    # S5 Piercing split (10.00–12.80): corte al beat + brillo especular sonoro
    add(fx, whoosh(0.42, 260, 6800, 1.5), 9.82, 0.32, 0.30)
    add(fx, impact(0.44, 94, 40, 0.60), 10.00, 0.46)
    add(fx, ping(0.55, 1860), 11.05, 0.16, 0.15)

    # S6 Packshot CTA (12.80–17.00): riser -> drop, pad limpio y campana del botón
    add(fx, riser(1.18), 11.60, 0.34)
    add(fx, impact(0.95, 108, 34, 1.25), 12.80, 0.95)
    add(fx, boom(1.80), 12.80, 0.54)
    add(fx, pad([220.0, 261.63, 329.63, 493.88], 4.05, 0.15), 12.86, 1.0)
    add(fx, shutter_tick(0.05, 2800), 12.96, 0.40, -0.15)
    add(fx, ping(1.05, 1245), 13.55, 0.42, 0.12)   # pop + shimmer del botón WhatsApp
    add(fx, ping(0.80, 1568), 15.40, 0.20, -0.10)  # segundo barrido especular

    mix = bed * 0.78 + fx * 0.85
    mix = np.tanh(mix * 1.55) * 0.95
    mix = mix / (np.abs(mix).max() + 1e-9) * 0.89

    tail = int(0.28 * SR)
    mix[-tail:] *= np.linspace(1.0, 0.0, tail)[:, None] ** 1.5
    mix += rng.normal(0.0, 1e-5, mix.shape).astype(np.float32)

    assert mix.shape[0] == total, mix.shape
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    wavfile.write(OUT, SR, (np.clip(mix, -1.0, 1.0) * 32767).astype(np.int16))
    rms_db = 20.0 * np.log10(np.sqrt((mix ** 2).mean()) + 1e-9)
    peak_db = 20.0 * np.log10(np.abs(mix).max() + 1e-9)
    print(f"Audio 17s masterizado: {OUT} ({DUR:.2f}s @ {SR}Hz estéreo, RMS={rms_db:.1f} dBFS, pico={peak_db:.1f} dBFS)")


if __name__ == "__main__":
    build()
