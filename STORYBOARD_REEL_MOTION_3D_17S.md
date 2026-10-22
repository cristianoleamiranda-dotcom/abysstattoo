# Storyboard de producción — Reel Motion Design 3D · Abyss Tattoo Studio

**Versión objetivo:** 17 s · vertical 9:16 · 1080×1920 · 60 fps · H.264/BT.709  
**Destino:** Instagram Reels, TikTok y WhatsApp  
**Objetivo:** mostrar tatuajes reales, proceso, estudio y piercing; cerrar con un CTA inequívoco.

> **Estado: render de 17 s EXPORTADO y verificado** (máster social 60 fps + copia ligera WhatsApp). Detalle completo, mediciones y copy de publicación en `ENTREGA_REEL_MOTION_3D_17S.md`. El MP4 de 15 s sigue publicado como versión anterior.

## Recursos del repositorio

- Placas visuales: `assets/reel_plates/`
- Trabajos: `assets/trabajos/`
- Fachada: `assets/estudio/fachada.jpg`
- Maestro / artista: `assets/estudio/maestro.jpg`
- Vitrina: `assets/estudio/vitrina.jpg`
- Emblema: `assets/reel_plates/emblema_abyss_alpha.png`
- Clips: `film/hero_film.mp4`, `film/loop_film.mp4`, `film/proceso_detalle.mp4`, `film/proceso_filmacion.mp4`, `film/proceso_pierna.mp4`
- Reel previo y storyboard anterior: `film/reel_comercial_abyss_15s_1080x1920_60fps_social.mp4`, `film/storyboard_reel_abyss_15s.jpg`

## Escaleta de 17 segundos

| Tiempo | Plano / material | Motion design y cámara virtual 3D | Texto en pantalla |
|---|---|---|---|
| 00:00–00:01.6 | Macro del proceso real o `proceso_detalle.mp4` | Crash zoom desde macro, profundidad/parallax, micro camera-shake; entrada inmediata en el primer frame | **EL ARTE SE LLEVA EN LA PIEL** |
| 00:01.6–00:04.2 | `plate_p02_lobo_samurai.jpg`, `plate_p03_hombro_realismo.jpg` | Push-in 3D y pull-back alternados; whip-pan sincronizado con el beat; conservar el tatuaje como protagonista | **PIEZAS ÚNICAS · DISEÑO AUTORAL** |
| 00:04.2–00:06.6 | `assets/estudio/fachada.jpg` y `assets/estudio/vitrina.jpg` | Dolly-in con tilt-up, capas separadas para parallax y líneas HUD discretas | **ABYSS TATTOO STUDIO** / **JOSÉ JOAQUÍN PÉREZ 528** |
| 00:06.6–00:10.0 | `proceso_filmacion.mp4`, `proceso_pierna.mp4` | Speed ramp breve, transición ink-wipe, cámara virtual con perspectiva 3D y etalonaje coherente | **TÉCNICA · DETALLE · PRECISIÓN** |
| 00:10.0–00:12.8 | `plate_p06_helix_titanio.jpg`, `plate_p07_septum_titanio.jpg` | Split-screen macro con movimientos opuestos, reflejo especular controlado y corte al beat | **TATUAJES · PIERCING · JOYERÍA** |
| 00:12.8–00:17.0 | Emblema oficial + mejor plano de portafolio como fondo | Pull-back final a composición limpia, emblema con settle elástico, brillo sutil sobre CTA; mantener texto legible | **RESERVA TU HORA** / **ESCRÍBENOS POR WHATSAPP** / **SAN BERNARDO · J. J. PÉREZ 528** |

## CTA

- Texto principal: **RESERVA TU HORA**
- Texto secundario: **ESCRÍBENOS POR WHATSAPP**
- Enlace de contacto: https://wa.me/56999674009?text=Cliente%20captado%20por%20Cristian%20Olea
- Ubicación: **José Joaquín Pérez 528, San Bernardo**
- No incrustar el enlace largo en el video; usar botón visual y dirigir al enlace desde la publicación/perfil.

## Dirección de arte y acabado

- Paleta: Obsidiana `#14100D`, Hueso `#B5A295`, Crema `#EAE3DD`, Verde Salvia `#556C65`.
- Movimiento: GSAP-like easing, parallax de planos, tilt 3D, crash zoom, push-in/pull-back, whip-pan y transiciones por máscara.
- Mantener tatuajes y joyería fieles a las fotos reales: no regenerar ni deformar diseños, anatomía, agujas o piezas.
- Corregir y unificar color a BT.709; negros profundos y tonos de piel naturales.
- Mantener títulos y CTA dentro de zonas seguras de Reels; dejar libres los controles laterales y la franja inferior de interfaz.
- Sonido: beat publicitario y foley sutil sincronizados a cortes; cierre sonoro limpio bajo el CTA.
- No reutilizar ofertas caducadas ni el número de dirección antiguo **548**.

## Checklist antes de exportar

1. Confirmar que cada clip y placa exista y se reproduzca.
2. Revisar que la fachada muestre la dirección correcta **528**.
3. Comprobar 17.00 s exactos, 1080×1920, 60 fps, H.264, BT.709 y AAC 48 kHz.
4. Verificar CTA, legibilidad móvil, sincronía de audio y ausencia de texto deformado.
5. Exportar el máster social y una copia ligera para WhatsApp.

## Entregables exportados según esta guía

| Archivo | Especificación medida |
|---|---|
| `film/reel_comercial_abyss_17s_1080x1920_60fps_social.mp4` | Máster social: 1080×1920 · 60 fps · 17.00 s (1020 frames) · H.264 High · BT.709 · AAC 48 kHz estéreo · 11.9 MB |
| `film/reel_comercial_abyss_17s_720x1280_30fps_whatsapp.mp4` | Copia ligera WhatsApp: 720×1280 · 30 fps · 17.00 s · BT.709 · AAC 48 kHz · 4.1 MB |
| `film/reel_comercial_abyss_17s_cover_hook.jpg` | Portada de gancho (t = 0.85 s) |
| `film/reel_comercial_abyss_17s_poster_cta.jpg` | Póster del CTA (t = 15.90 s) |
| `film/storyboard_reel_abyss_17s.jpg` | Hoja de contacto de la escaleta (S1–S6) extraída del render |

Reproducción del render:

```bash
.venv/bin/python scripts/build_reel_audio_17s.py   # audio 17.00 s / 48 kHz autocontenido
.venv/bin/python scripts/build_reel_17s.py         # máster + copia WhatsApp + portadas + storyboard
.venv/bin/python scripts/ci_audit_deliverables.py  # auditoría de másters y marca (528)
```
