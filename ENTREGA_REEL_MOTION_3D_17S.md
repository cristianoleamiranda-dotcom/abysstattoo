# Entrega — Reel Motion Design 3D 17 s · Abyss Tattoo Studio

**Fecha de render:** 2026-10-22 · **Guía de montaje:** `STORYBOARD_REEL_MOTION_3D_17S.md`
**Destino:** Instagram Reels, TikTok y WhatsApp · **Ubicación oficial:** José Joaquín Pérez 528, San Bernardo

## Entregables (medidos sobre los archivos codificados)

| Archivo | Especificación medida |
|---|---|
| `film/reel_comercial_abyss_17s_1080x1920_60fps_social.mp4` | **Máster social** — 1080×1920 · 60 fps · **17.00 s exactos (1020 frames)** · H.264 High · BT.709 (primaries/transfer/matrix) · AAC LC 192 kbps · 48 kHz estéreo · `+faststart` · 12 449 028 bytes (11.9 MB) |
| `film/reel_comercial_abyss_17s_720x1280_30fps_whatsapp.mp4` | **Copia ligera WhatsApp** — 720×1280 · 30 fps · 17.00 s (510 frames) · H.264 High · BT.709 · AAC 128 kbps · 48 kHz · 4 286 133 bytes (4.1 MB) |
| `film/reel_comercial_abyss_17s_cover_hook.jpg` | Portada de gancho para la cuadrícula de Reels (frame t = 0.85 s) |
| `film/reel_comercial_abyss_17s_poster_cta.jpg` | Póster del packshot CTA (frame t = 15.90 s) |
| `film/storyboard_reel_abyss_17s.jpg` | Hoja de contacto S1–S6 extraída del propio render (3×3) |
| `film/reel_abyss_17s_audio.wav` | Mezcla maestra 17.00 s · 48 kHz estéreo (autocontenida, sin fuentes externas) |

Sala de proyección: `reel.html` (pestaña principal **«9:16 · NUEVO Motion 3D 17s»**, escaleta interactiva S1–S6 y descargas).

## Escaleta ejecutada

| Tiempo | Material real | Motion 3D aplicado | Texto en pantalla |
|---|---|---|---|
| 00:00–00:01.6 | `proceso_detalle.mp4` (ss 4.05 s, HLG 10-bit → BT.709) | Crash zoom (z 1.14→1.36) sobre la punta de la aguja, blur radial de entrada, micro-shake, foco medido (0.57–0.56 · 0.40–0.50) | **EL ARTE SE LLEVA / EN LA PIEL** |
| 00:01.6–00:04.2 | `plate_p02_lobo_samurai.jpg` → `plate_p03_hombro_realismo.jpg` (corte interno 2.90 s) | Push-in 3D con roll / pull-back inverso, whip-pan + flash al beat | **PIEZAS ÚNICAS · DISEÑO AUTORAL** |
| 00:04.2–00:06.6 | `plate_p01_fachada_real.jpg` (← `fachada.jpg`) → `plate_p08_vitrina_estudio.jpg` (← `vitrina.jpg`) | Dolly-in con tilt-up y perspectiva 3D, capa HUD independiente (parallax), callout «DIRECCIÓN OFICIAL · J. J. PÉREZ 528» | **ABYSS TATTOO STUDIO / JOSÉ JOAQUÍN PÉREZ 528** |
| 00:06.6–00:10.0 | `proceso_filmacion.mp4` (ss 2.35 s) → `proceso_pierna.mp4` (ss 1.15 s) | Speed ramp en el muestreo fuente de ambos clips, **ink-wipe** diagonal en 8.30 s, perspectiva 3D en el segundo plano | **TÉCNICA / DETALLE / PRECISIÓN** (revelado palabra a palabra) |
| 00:10.0–00:12.8 | `plate_p06_helix_titanio.jpg` / `plate_p07_septum_titanio.jpg` | Split-screen con banda central; pull-back arriba / push-in abajo (opuestos), barrido especular diagonal controlado; centros medidos sobre grilla (gemas hélix 0.47·0.27; arco septum y 0.50–0.67) | **TATUAJES · PIERCING · JOYERÍA** (+ tags HÉLIX / SEPTUM) |
| 00:12.8–00:17.0 | `emblema_abyss_alpha.png` sobre fondo del plano lobo/samurái desenfocado en Obsidiana | Pull-back a composición limpia, emblema con settle elástico + flotación, halo/anillos, botón con doble shimmer (0.95 s y 2.60 s locales) | **RESERVA TU HORA / ESCRÍBENOS POR WHATSAPP** (botón) **/ @abyss_tattoo_studio / SAN BERNARDO · J. J. PÉREZ 528** |

**Sonido** (`scripts/build_reel_audio_17s.py`, sin depender de archivos externos): beat publicitario sintetizado a **100 BPM** (bombo/clap/hats, bajo, arpegio y pad en La menor) con bombeo sidechain y ducking en los cortes 1.60 / 4.20 / 6.60 / 8.30 / 10.00; foley de máquina rotativa en los macros (0.05 s, 6.66 s, 8.38 s); whooshes y obturadores en cada corte; riser 11.60–12.80 → impacto + sub-boom en 12.80; pad limpio bajo el CTA y campana al encenderse el botón (13.55 s) y en el segundo shimmer (15.40 s). Medición del máster: **−16.7 LUFS integrado · pico −1.0 dBFS** (WAV).

## Checklist de la guía — resultado

1. ✅ **Cada clip y placa existe y se reproduce**: preflight automático en el builder (decode de los 3 clips: 240/196/166 frames @30 fps; verificación PIL de placas, estudio y emblema; WAV 17 s presente).
2. ✅ **Dirección 528**: la fachada real es `assets/estudio/fachada.jpg` y los rótulos dicen «JOSÉ JOAQUÍN PÉREZ 528» (S3), callout «J. J. PÉREZ 528» y pastilla «SAN BERNARDO · J. J. PÉREZ 528» (CTA). Sin «548» ni ofertas caducadas en los scripts de 17 s (verificado por grep y por `ci_audit_deliverables.py`).
3. ✅ **17.00 s / 1080×1920 / 60 fps / H.264 / BT.709 / AAC 48 kHz**: medido en el archivo final (1020 frames contados, duración de contenedor 17.00, tags BT.709 en video, AAC 48000 Hz estéreo). Auditoría CI local: **APROBADO 0 errores (6/6 másters OK, 49 referencias locales intactas)**; CI la repetirá en el PR.
4. ✅ **CTA y legibilidad móvil**: todos los títulos validados ≤ 900 px de ancho centrados (x ∈ [90, 990]) y dentro de la banda segura superior/central; franja inferior e iconos laterales de Reels libres. Frames del MP4 codificado revisados visualmente en t = 0.02 / 1.55 / 4.25 / 8.30 / 10.05 / 12.85 / 14.20 / 16.95; `blackdetect` sin tramos negros; primer frame con contenido inmediato.
5. ✅ **Máster social + copia ligera WhatsApp** exportados (tabla superior), ambos con `+faststart`.

Notas de fidelidad: no se regeneró ni deformó ningún tatuaje, joya ni anatomía — solo cámara virtual 3D (warp proyectivo sub-píxel), etalonaje y tipografía sobre el material real. El arco del septum viene recortado por el borde izquierdo en la foto original (`septum.jpg`); el encuadre lo respeta sin espejar contenido.

## Publicación

- **Reels/TikTok**: subir `reel_comercial_abyss_17s_1080x1920_60fps_social.mp4`; portada `reel_comercial_abyss_17s_cover_hook.jpg`.
- **WhatsApp (estados/catalogación)**: enviar `reel_comercial_abyss_17s_720x1280_30fps_whatsapp.mp4` (4.1 MB).
- **CTA clicable** (no va incrustado en el video, según la guía — usar en bio/enlace de la publicación o sticker de enlace):
  https://wa.me/56999674009?text=Cliente%20captado%20por%20Cristian%20Olea

> ⚠️ **Aviso de consistencia**: el enlace de captación indicado en la guía apunta al número **+56 9 9967 4009**, mientras el sitio (`index.html`, `reel.html`) y el reel de 15 s usan el WhatsApp del estudio **+56 9 4778 6839**. En el video de 17 s no se imprimió ningún número (solo el botón «ESCRÍBENOS POR WHATSAPP»), por lo que el máster sirve con cualquiera de los dos enlaces; confirma cuál debe quedar en el perfil antes de publicar.

### Copy listo para pegar

```text
El arte se lleva en la piel. ♦

Piezas únicas y diseño autoral en Abyss Tattoo Studio: tatuajes, piercing y joyería.
Técnica · Detalle · Precisión — trabajo real, de nuestro estudio.

📍 José Joaquín Pérez 528, San Bernardo
📲 Reserva tu hora: escríbenos por WhatsApp (enlace en el perfil)
@abyss_tattoo_studio

#AbyssTattooStudio #TatuajesChile #SanBernardo #TatuajesSantiago #RealismoBlackAndGrey #Piercing #JoyeriaTitanio
```

## Cómo reproducir o ajustar el render

```bash
python3 -m venv .venv
.venv/bin/pip install opencv-python-headless numpy pillow scipy imageio-ffmpeg
cp "$(.venv/bin/python -c 'import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())')" .venv/bin/ffmpeg

.venv/bin/python scripts/build_reel_audio_17s.py    # WAV 17.00 s
.venv/bin/python scripts/build_reel_17s.py --proofs # lámina de pruebas sin codificar (opcional)
.venv/bin/python scripts/build_reel_17s.py          # máster + WhatsApp + portadas + storyboard
.venv/bin/python scripts/ci_audit_deliverables.py   # auditoría de másters y marca
```

Las placas de video intermedias se derivan automáticamente en `/tmp/abyss_17s_plates/` desde `film/proceso_*.mp4` reutilizando el tone-mapping HLG→BT.709 y el etalonaje LightCraft de `scripts/prepare_commercial_assets.py` (no requieren archivos externos al repositorio).
