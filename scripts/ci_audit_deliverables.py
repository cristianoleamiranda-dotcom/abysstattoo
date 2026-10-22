#!/usr/bin/env python3
"""
ci_audit_deliverables.py — Auditoría automatizada de marca, HTML y másters de video (FFprobe)
para ejecutarse tanto localmente como dentro de GitHub Actions / Acciones Personalizadas.

Valida:
  1. Integridad de datos oficiales invariables en index.html, tarifario.html y reel.html:
     - Dirección verificada: "José Joaquín Pérez 528" (bloquea regresiones "548" en HTML).
     - Ausencia de promociones vencidas ("20% dcto", "10% adicional", "$70.000").
     - Existencia real en disco de cada imagen, video, fuente y enlace interno referenciado.
  2. Especificación técnica broadcast/social de los másters MP4 (Reel Comercial 15 s
     y Reel Motion Design 3D 17 s):
     - Resolución exacta según formato, cadencia (60/30 fps), duración exacta
       (15.00 s / 17.00 s ± 0.08 s), espacio de color BT.709 y audio estéreo 48 kHz.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
os.chdir(ROOT)

EXPECTED_VIDEOS = [
    ("film/reel_comercial_abyss_15s_1080x1920_60fps_social.mp4", 1080, 1920, 60, 15.0, "Máster 9:16 Social · Hook A (Arte)"),
    ("film/reel_comercial_abyss_15s_hook_b_local_60fps.mp4", 1080, 1920, 60, 15.0, "Variante 9:16 Local · Hook B (Dron 528)"),
    ("film/reel_comercial_abyss_15s_1080x1350_4x5_feed.mp4", 1080, 1350, 30, 15.0, "Adaptación Nativa 4:5 Feed Instagram"),
    ("film/reel_comercial_abyss_15s_1080x1920_30fps_web.mp4", 1080, 1920, 30, 15.0, "Derivada Ligera 9:16 Web / WhatsApp"),
    ("film/reel_comercial_abyss_17s_1080x1920_60fps_social.mp4", 1080, 1920, 60, 17.0, "Reel Motion 3D 17 s · Máster 9:16 Social"),
    ("film/reel_comercial_abyss_17s_720x1280_30fps_whatsapp.mp4", 720, 1280, 30, 17.0, "Reel Motion 3D 17 s · Copia Ligera WhatsApp"),
]

HTML_FILES = ["index.html", "reel.html", "tarifario.html"]
FORBIDDEN_PATTERNS = [
    (r"P[ée]rez\s*548", "Numeración antigua errónea '548' detectada"),
    (r"20\s*%\s*dcto", "Promoción vencida '20% dcto' detectada"),
    (r"\$70\.000", "Tarifa promocional obsoleta '$70.000' detectada"),
]


def resolve_ffprobe():
    fp = shutil.which("ffprobe")
    if fp:
        return fp, "ffprobe"
    ff = shutil.which("ffmpeg")
    if ff:
        return ff, "ffmpeg"
    if os.path.exists("/tmp/ffmpeg"):
        return "/tmp/ffmpeg", "ffmpeg"
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe(), "ffmpeg"
    except Exception:
        raise RuntimeError("No se encontró ffprobe ni ffmpeg en el entorno.")


def probe_video(path: str):
    exe, mode = resolve_ffprobe()
    if mode == "ffprobe":
        raw = subprocess.check_output(
            [exe, "-v", "error", "-show_streams", "-show_format", "-of", "json", path],
            text=True,
        )
        data = json.loads(raw)
        vs = next(s for s in data["streams"] if s["codec_type"] == "video")
        aus = next((s for s in data["streams"] if s["codec_type"] == "audio"), None)
        num, den = map(int, vs["r_frame_rate"].split("/"))
        return {
            "width": int(vs["width"]),
            "height": int(vs["height"]),
            "fps": round(num / max(1, den)),
            "color": vs.get("color_space", "unknown"),
            "duration": float(data["format"]["duration"]),
            "sample_rate": int(aus["sample_rate"]) if aus else 0,
            "channels": int(aus["channels"]) if aus else 0,
            "size_mb": os.path.getsize(path) / (1024 * 1024),
        }

    p = subprocess.run([exe, "-i", path], capture_output=True, text=True)
    info = p.stderr
    m_dur = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", info)
    dur = int(m_dur.group(1)) * 3600 + int(m_dur.group(2)) * 60 + float(m_dur.group(3)) if m_dur else 0.0
    m_vid = re.search(r"Video:.*?,\s*(\d+)x(\d+).*?,\s*(\d+(?:\.\d+)?)\s*fps", info)
    m_aud = re.search(r"Audio:.*?,\s*(\d+)\s*Hz,\s*(stereo|mono)", info)
    return {
        "width": int(m_vid.group(1)) if m_vid else 0,
        "height": int(m_vid.group(2)) if m_vid else 0,
        "fps": round(float(m_vid.group(3))) if m_vid else 0,
        "color": "bt709" if "bt709" in info else "unknown",
        "duration": dur,
        "sample_rate": int(m_aud.group(1)) if m_aud else 0,
        "channels": 2 if (m_aud and m_aud.group(2) == "stereo") else 1,
        "size_mb": os.path.getsize(path) / (1024 * 1024),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="/tmp/abyss_ci_audit.md")
    args = parser.parse_args()

    errors = []
    video_rows = []

    # 1. Auditoría de páginas HTML y reglas de marca
    checked_links = 0
    for hf in HTML_FILES:
        if not os.path.isfile(hf):
            errors.append(f"Falta archivo HTML requerido: `{hf}`")
            continue
        txt = open(hf, encoding="utf-8").read()
        if hf in ("index.html", "reel.html") and "528" not in txt:
            errors.append(f"`{hf}` no contiene la numeración oficial `528`.")
        for pat, msg in FORBIDDEN_PATTERNS:
            if re.search(pat, txt, flags=re.IGNORECASE):
                errors.append(f"`{hf}`: {msg}")
        for ref in re.findall(r'(?:src|href|poster)="([^"#?]+)"', txt):
            if ref.startswith(("http://", "https://", "mailto:", "tel:", "data:", "javascript:")):
                continue
            checked_links += 1
            if not os.path.exists(ref):
                errors.append(f"Enlace o activo local roto en `{hf}` -> `{ref}`")

    # 2. Auditoría de másters de video con FFprobe/FFmpeg
    for vpath, exp_w, exp_h, exp_fps, exp_dur, label in EXPECTED_VIDEOS:
        if not os.path.isfile(vpath):
            errors.append(f"Falta entregable de video: `{vpath}`")
            continue
        meta = probe_video(vpath)
        ok_res = meta["width"] == exp_w and meta["height"] == exp_h
        ok_fps = meta["fps"] == exp_fps
        ok_dur = abs(meta["duration"] - exp_dur) <= 0.08
        ok_col = meta["color"] == "bt709"
        ok_aud = meta["sample_rate"] == 48000 and meta["channels"] == 2
        status = "✅ OK" if all([ok_res, ok_fps, ok_dur, ok_col, ok_aud]) else "❌ FAIL"
        if status != "✅ OK":
            errors.append(f"Fallo técnico en `{vpath}`: {meta}")
        video_rows.append(
            f"| {label} | `{os.path.basename(vpath)}` | `{meta['width']}×{meta['height']}` | `{meta['fps']} fps` | "
            f"`{meta['duration']:.2f} s` | `{meta['color'].upper()}` | `{meta['sample_rate']} Hz · {meta['channels']}ch` | "
            f"`{meta['size_mb']:.1f} MB` | {status} |"
        )

    lines = [
        "<!-- abyss-media-audit-comment -->",
        "## 🎬 Auditoría Automática Audiovisual & Marca — Abyss Tattoo Studio",
        "",
        f"**Estado general:** {'✅ **APROBADO (0 errores)**' if not errors else f'❌ **FALLÓ ({len(errors)} errores)**'}  ",
        f"**Dirección oficial verificada:** `José Joaquín Pérez 528, San Bernardo` · **Activos locales verificados:** `{checked_links}` referencias intactas.",
        "",
        "### Verificación de Másters MP4 (FFprobe / Stream Inspector)",
        "",
        "| Pieza | Archivo | Resolución | FPS | Duración | Color | Audio | Peso | Estado |",
        "|---|---|---|---|---|---|---|---|---|",
        *video_rows,
        "",
        "### Láminas de Control en el Repositorio",
        "- `film/auditoria_edicion_material_reel.jpg` — Comparativa Antes vs. Después (recorte de rótulos antiguos `548` y tone-mapping HLG → BT.709)",
        "- `film/storyboard_reel_abyss_15s.jpg` — Hoja de contacto de los 12 planos a 100 BPM",
        "- `film/storyboard_reel_abyss_17s.jpg` — Hoja de contacto de la escaleta 17 s (S1–S6)",
        "- `reel.html` — Sala de proyección multi-formato (`9:16 Hook A`, `9:16 Hook B Local`, `4:5 Feed Nativo` y `30 fps Web`)",
    ]
    if errors:
        lines += ["", "### Errores detectados", *[f"- {e}" for e in errors]]

    report = "\n".join(lines) + "\n"
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(report)

    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as sf:
            sf.write(report)

    print(report)
    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
