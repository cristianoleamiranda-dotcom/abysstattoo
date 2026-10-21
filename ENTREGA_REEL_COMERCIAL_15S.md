# Entrega — Reel Comercial 15 s · Abyss Tattoo Studio

**Fecha:** 21 de octubre de 2026
**Pieza:** comercial vertical 9:16 de 15,00 s para Reels / TikTok / Meta Ads
**Estudio:** Abyss Tattoo Studio — José Joaquín Pérez 528, San Bernardo, RM · desde 2009
**Contacto en pantalla:** WhatsApp +56 9 4778 6839 · @abyss_tattoo_studio

---

## 1. Archivo principal

| Archivo | Formato | Peso | Para qué |
|---|---|---|---|
| `film/reel_comercial_abyss_15s_1080x1920_60fps_master.mp4` | 1080×1920 · 60 fps · ~100 Mbps · AAC 48 kHz | ~195 MB | máster de archivo y futuras re-ediciones |
| `film/reel_comercial_abyss_15s_1080x1920_60fps_social.mp4` | 1080×1920 · 60 fps · ~14 Mbps | ~28 MB | **publicar en Instagram / TikTok / Meta Ads** |
| `film/reel_comercial_abyss_15s_1080x1920_30fps_web.mp4` | 1080×1920 · 30 fps · ~6 Mbps | ~11 MB | web, WhatsApp, correo |
| `film/reel_comercial_abyss_15s_cover_hook.jpg` | 1080×1920 | 84 KB | portada del reel |
| `film/reel_comercial_abyss_15s_poster_cta.jpg` | 1080×1920 | 69 KB | póster del CTA / story estático |
| `film/storyboard_reel_abyss_15s.jpg` | 1594×2658 | — | guion gráfico con timecodes |
| `film/auditoria_edicion_material_reel.jpg` | 1700×1180 | — | auditoría antes/después del material crudo |
| `film/reel_abyss_15s_audio.wav` | WAV 48 kHz estéreo | 11 MB | pista masterizada |

## 2. Guion final (lo que se ve y se lee)

| TC | Imagen | Copy en pantalla |
|---|---|---|
| 0,00–1,20 | macro de aguja entrando en la piel | ESTO NO ES / **UN TATUAJE.** |
| 1,20–2,40 | primer plano lobo + espartano | **ES UNA FIRMA.** / REALISMO BLACK & GREY |
| 2,40–4,20 | fachada diurna con mural | SAN BERNARDO · CHILE / **DESDE 2009** / JOSÉ JOAQUÍN PÉREZ 528 |
| 4,20–5,40 | pasillo interior, travelling | **ENTRA.** / UN ESTUDIO, NO UNA VITRINA. |
| 5,40–6,60 | artista tatuando en camilla | **CABINA CLÍNICA** / AGUJAS SELLADAS · PROTOCOLO SEREMI |
| 6,60–7,80 | macro de sombreado en vivo | **REALISMO** / BLACK & GREY |
| 7,80–9,00 | detalle hombro ornamental | **PIEZA ÚNICA** / DISEÑO PERSONALIZADO SIN PLANTILLAS |
| 9,00–10,20 | antebrazo manga completa | **SIN PLANTILLAS** / CADA PIEZA SE DISEÑA PARA TI |
| 10,20–11,40 | split: hélix + septum | **TITANIO** / ASTM F136 · GRADO IMPLANTE / PERFORACIÓN CLÍNICA |
| 11,40–12,60 | artista en sesión, plano medio | **5 ARTISTAS** / UN MISMO ESTÁNDAR |
| 12,60–15,00 | emblema Abyss sobre mural desenfocado | **AGENDA TU HORA** / ◆ WHATSAPP +56 9 4778 6839 / @abyss_tattoo_studio / JOSÉ JOAQUÍN PÉREZ 528 · SAN BERNARDO / ESCRIBE Y COORDINAMOS TU HORA |

Total de copy hablado/leído en pantalla: **≈ 45 palabras**, dentro del rango recomendado (35–55) para 15 segundos.

## 3. Material de origen utilizado

| Fuente | Uso | Tratamiento |
|---|---|---|
| `story_abyss_15s.mp4` (link tmpfiles) | referencia de estructura del story anterior | **no se usó su versión editada**: se rehizo desde el máster limpio |
| `story_ubicacion_aerea_abyss_1080p.mp4` (Dropbox) | dron de San Bernardo, fachada, pasillo | recorte de rótulos quemados + etalonaje |
| `film/hero_film.mp4`, `proceso_detalle.mp4`, `proceso_filmacion.mp4`, `proceso_pierna.mp4` | macro, cabina, sesión | conversión HLG/HDR → BT.709 + reencuadre |
| `assets/estudio/fachada.jpg`, `maestro.jpg`, `vitrina.jpg` | mural, artista, vitrina | reencuadre 9:16 + curva de color |
| `assets/trabajos/*.jpg` | portafolio y piercing | reencuadre 9:16 + etalonaje unificado |
| Identidad de marca (Dropbox) | emblema, paleta, tipografías | `Cinzel` + `Montserrat` instanciadas en pesos estáticos |

**Descartado a propósito:** las tarjetas promocionales antiguas (`20 % / 10 % / $70.000`), la captura de Instagram y las miniaturas con interfaz móvil. Un comercial nuevo no hereda la campaña anterior.

## 4. Cumplimiento de la identidad

- Tipografías oficiales: `Cinzel` (titulares) y `Montserrat` (UI y datos), instanciadas desde los archivos variables del sitio.
- Paleta: obsidiana `#14100D` / `#1E1B18`, hueso `#B5A295`, crema `#EAE3DD`, papel `#F6F1ED`, verde salvia `#556C65` como único acento.
- Emblema circular oficial con alfa, usado en el cierre.
- Datos verificados: dirección **528** (no 548), WhatsApp **+56 9 4778 6839**, usuario **@abyss_tattoo_studio**, año de fundación **2009**.
- Sin promociones, sin precios y sin textos heredados.

## 5. Cómo se reproduce o se ajusta

```bash
# curaduría + etalonaje (una sola vez, ~2 min)
.venv/bin/python scripts/prepare_commercial_assets.py
# pista de audio (~5 s)
.venv/bin/python scripts/build_reel_audio.py
# montaje + export (~6 min a 60 fps)
.venv/bin/python scripts/build_reel_commercial.py --fps 60 \
  --out film/reel_comercial_abyss_15s_1080x1920_60fps_master.mp4
# guion gráfico
.venv/bin/python scripts/build_storyboard.py
```

Textos, tiempos de plano y movimientos de cámara viven en `scripts/build_reel_commercial.py`
(`make_timeline()` y `build_graphics()`), así que cualquier ajuste de copy o de duración se hace ahí y se
vuelve a renderizar sin tocar los activos.

## 6. Recomendaciones de publicación

1. Subir el archivo **`_social.mp4`** como Reel con la portada `_cover_hook.jpg`.
2. Primer comentario con dirección + link `wa.me/56947786839`.
3. Ubicación etiquetada: José Joaquín Pérez 528, San Bernardo.
4. Copy corto: una sola instrucción (“escríbenos por WhatsApp y coordinamos tu hora”) + 3 a 5 hashtags locales.
5. Probar dos hooks (A: “Esto no es un tatuaje”; B: “Antes de tatuarte, mira esto”) y dejar el de mayor retención a 3 s.
6. Si se pauta: objetivo *Mensajes*, ubicaciones Reels + Stories, y este creativo como pieza principal.

La guía metodológica completa —cómo se convierte un reel en comercial, gramática de planos, tiros de cámara,
zooms, diseño sonoro y checklist de medición— está en **`REEL_A_COMERCIAL_GUIA.md`**.
