# Entrega — Reel Comercial de 15 Segundos · Abyss Tattoo Studio

## 1. Archivos finales entregados

| Archivo | Especificación | Uso recomendado |
|---|---|---|
| `film/reel_comercial_abyss_15s_1080x1920_60fps_social.mp4` | `1080×1920` (9:16) · **15.00 s exactos (900 frames)** · **60 fps** · H.264 High L4.2 BT.709 · AAC 48 kHz 192 kbps · `faststart` | **Máster principal para subir a Instagram Reels, TikTok y Meta Ads** |
| `film/reel_comercial_abyss_15s_1080x1920_30fps_web.mp4` | `1080×1920` (9:16) · **15.00 s exactos (450 frames)** · **30 fps** · H.264 High BT.709 · AAC 48 kHz 160 kbps | Reproducción instantánea en web (`reel.html`) y envío por WhatsApp |
| `film/reel_comercial_abyss_15s_cover_hook.jpg` | `1080×1920` JPEG de alta calidad | Portada (Cover) del Reel en el perfil de Instagram |
| `film/reel_comercial_abyss_15s_poster_cta.jpg` | `1080×1920` JPEG de alta calidad | Historia estática de refuerzo con CTA directo y dirección **528** |
| `film/storyboard_reel_abyss_15s.jpg` | `2058×1446` Hoja de contacto de los 12 planos | Validación visual completa cuadro a cuadro |
| `film/auditoria_edicion_material_reel.jpg` | `2080×1240` Comparativa Antes / Después | Evidencia de auditoría, descarte, recorte y etalonaje previo al montaje |
| `REEL_A_COMERCIAL_GUIA.md` | Guía estratégica y cinematográfica | Metodología de conversión de Reel a Spot Comercial de 15 s |
| `reel.html` | Sala de revisión web interactiva | Reproductor en vivo 60 fps + ficha técnica + storyboard |

---

## 2. Auditoría, selección y edición previa del material (antes de montar)

Antes de construir la línea de tiempo se inspeccionaron todos los activos audiovisuales suministrados (videos de referencia, stories previas, clips de sesión en cabina, capturas y fotografías de portafolio):

1. **Corrección estricta de dirección oficial (`Es 528`)**:
   - Los videos anteriores (`story_abyss_15s.mp4` y `story_ubicacion_aerea1.mp4`) tenían incrustada en imagen una numeración errónea (`548`). Se recortaron por completo las bandas quemadas superiores e inferiores mediante una ventana `9:16` exacta (`675×1200` escalada con Lanczos-4 a `1296×2304`), y toda la señalética, HUD, subtítulos y Packshot CTA fueron construidos con la dirección oficial verificada: **José Joaquín Pérez 528, San Bernardo**.
2. **Descarte de promociones pasadas, textos deformados e interfaces de captura**:
   - Se descartaron las tarjetas promocionales obsoletas (`20% DCTO / 10% DCTO / $70.000 CLP / Marcos Salinas`), capturas de pantalla con interfaz móvil de Instagram y miniaturas comprimidas `< 65 KB`, así como los cuadros transicionales con texto deformado por IA, sustituyéndolos por la fotografía callejera real verificada de la fachada del estudio (`assets/estudio/fachada.jpg`) y tomas reales de video en cabina.
3. **Conversión HDR HLG 10-bit → BT.709 SDR y Etalonaje LightCraft**:
   - El material de sesión `proceso_detalle.mp4` venía en espacio `bt2020nc / arib-std-b67` (HLG 10-bit), provocando sobreexposición anaranjada en tonos de piel al mezclarse con SDR. Se programó un operador de compresión suave de rodilla (*soft-knee tone-mapping*) a `BT.709`, recuperando tonos naturales de piel y negros profundos en el **Ink Wipe Reveal**.
   - Las **16 placas seleccionadas** (8 placas de video real en movimiento + 8 fotografías de alta resolución) fueron unificadas en micro-contraste LAB + *split-toning* Obsidiana `#14100D` / Hueso `#B5A295` / Verde Salvia `#556C65` con **+20 % de overscan (`1296×2304`)** para habilitar movimientos de cámara 3D sin bordes ni pérdida de nitidez.

---

## 3. Escaleta cinematográfica de 12 planos (Zooms, Tiros de Cámara y Escalas de Plano)

| # | Tiempo | Escala de Plano & Óptica | Tiro / Ángulo & Movimiento de Cámara 3D | Material Curado | Texto Cinético / Conversión |
|---|---|---|---|---|---|
| **01** | `0.00 – 1.20 s` | **ECU Macro · 100mm** | Rasante macro · *Crash Zoom Pull-Back* (`1.38→1.12`) + *radial blur* + vibración orgánica | Video real aguja en piel | `ESTO NO ES` / **`UN TATUAJE.`** |
| **02** | `1.20 – 2.40 s` | **Primer Plano · 50mm** | Contrapicado *chiaroscuro* · *Punch Zoom-In* con *speed-ramp* + *Whip-Pan X* | Video real hombro oscuro | **`ES UNA FIRMA.`** / `ARTE EN LA PIEL · DESDE 2009` |
| **03** | `2.40 – 3.60 s` | **Gran Plano Aéreo · Dron 16mm** | Picado aéreo FPV · *Hyper-Dive* descendente + inclinación 3D | Video real dron San Bernardo | Callout + **`JOSÉ JOAQUÍN PÉREZ 528`** |
| **04** | `3.60 – 4.50 s` | **Plano General · 24mm** | Nivel de calle frontal · *Dolly-In* + *Tilt-Up* en perspectiva 3D | Foto real fachada **528** | **`DESDE 2009`** / `JOSÉ JOAQUÍN PÉREZ 528` |
| **05** | `4.50 – 5.40 s` | **Travelling Subjetivo POV · 24mm** | Punto de fuga interior · Avance gimbal continuo + *Whip vertical Y* | Video real pasillo y vitrina | **`CRUZA LA PUERTA`** / `PRIVACIDAD · DISEÑO · RIGOR CLÍNICO` |
| **06** | `5.40 – 6.60 s` | **Plano Cenital Picado · 35mm** | Picado `60°` · Órbita suave (`-1.8°→+0.5°`) + *Push-In* | Video real cabina estéril | **`ZONA SEREMI`** / `CABINA ESTÉRIL · AGUJAS SELLADAS` |
| **07** | `6.60 – 7.80 s` | **PPP Detalle · 85mm** | *Over-the-Shoulder* · *Push-In* íntimo sobre limpieza de tinta en vivo | Video real *Ink Wipe* HDR→SDR | **`TRAZO A TRAZO`** / `SOMBRAS PROFUNDAS · CURADO PERFECTO` |
| **08** | `7.80 – 9.00 s` | **Detalle Realismo · 50mm** | Corte rítmico al pulso (`0.60 s`): *Crash Zoom-In* (`08a`) vs *Pull-Back* (`08b`) | Portafolio *Black & Grey* | **`PIEZA ÚNICA`** / `REALISMO BLACK & GREY · SIN PLANTILLAS` |
| **09** | `9.00 – 10.20 s` | **Plano Manga & Color · 35/50mm** | *Tilt* vertical ascendente en manga (`09a`) + *Whip* a *Full Color* (`09b`) | Manga B&G + *Full Color* | **`DISEÑO AUTORAL`** / `BLACK & GREY · ORIENTAL · FULL COLOR` |
| **10** | `10.20 – 11.40 s` | **Split-Screen Doble Macro · 100mm** | Pantalla dividida horizontal con zooms cruzados antagónicos | Hélix + Septum Titanio F136 | **`TITANIO ASTM F136`** / `PIERCING CLÍNICO · GRADO IMPLANTE` |
| **11** | `11.40 – 12.60 s` | **Plano Medio Lateral · 50mm** | Nivel de mirada · *Dolly Push-In* + *Riser* de tensión hacia el cierre | Video real artista en cabina | **`5 ARTISTAS`** / `UN MISMO ESTÁNDAR DE EXCELENCIA` |
| **12** | `12.60 – 15.00 s` | **Packshot Comercial CTA** | Emblema circular con *settle* elástico + botón con brillo especular (*shimmer*) | Sello oficial + cierre de marca | **`AGENDA TU HORA`** · **`WHATSAPP +56 9 4778 6839`** · **`@abyss_tattoo_studio`** · **`J. J. PÉREZ 528`** |
