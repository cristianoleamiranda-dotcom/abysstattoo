# Ficha técnica — Motion Poster 2.5D de Abyss Tattoo Studio

## Entrega

- **Vista previa:** [`promo-motion.html`](promo-motion.html)
- **Video:** `film/abyss_promocion_motion_10s_1080x1920_60fps_hq.mp4`
- **Portada vertical:** `film/abyss_promocion_motion_cover.jpg`
- **Afiche corregido, PNG sin pérdida:** `assets/promocion/abyss-promo-corrected.png` (2048 × 2048)
- **Original conservado:** `assets/promocion/abyss-promo-source.jpeg`
- **Master:** 10 s · 1080 × 1920 · 9:16 · 60 fps · MP4/H.264 High · BT.709 · CRF 14 · sin audio
- **Generación reproducible:** `scripts/correct_promo_copy.py` y `scripts/build_promo_motion.py`

La errata «echas» se corrigió a «hechas» en el afiche final; el original adjunto se conserva sin modificar. El video queda mudo deliberadamente para poder añadir audio propio/licenciado al publicar.

## Investigación aplicada

### 1. Parallax fotográfico y 2.5D

La guía de Adobe para animar una fotografía explica el flujo habitual: aislar elementos de primer plano, reconstruir lo que queda oculto, separar los planos en profundidad Z y mover una cámara virtual. La diferencia de movimiento entre planos es la que construye el parallax. En este caso se optó por una versión conservadora: el afiche íntegro es el plano frontal y una copia ampliada, oscurecida y desenfocada funciona como fondo lejano. Así se mantiene intacto el tatuaje y la tipografía, sin bordes de máscara inventados.

**Límite técnico importante:** el resultado es una ilusión **2.5D**, hecha con perspectiva y dos planos; no es geometría 3D real ni un mapa de profundidad volumétrico. Para girar el brazo fuera del plano harían falta máscaras manuales, reconstrucción de las zonas ocultas y/o un mapa de profundidad validado.

### 2. Cámara, keyframes y easing

La cámara pasa por posiciones clave: afiche completo → ojos del tatuaje → tramos del 35 %, 20 % y 10 % → composición completa. Los movimientos emplean curvas suaves de aceleración y frenado, en vez de desplazamiento lineal constante. Esto dirige la mirada y mantiene legibles los momentos donde aparecen los porcentajes.

### 3. Motion design y jerarquía

Se prioriza el tatuaje como imagen gancho, después los tres beneficios y, al final, el afiche completo. Los filetes dorados, la sombra de tarjeta y los destellos breves son acciones secundarias: acompañan la composición, pero no cubren el texto. La cámara no aplica deformación generativa al diseño ni al cuerpo.

### 4. Accesibilidad de la vista web

La página de revisión pausa el video si el dispositivo declara `prefers-reduced-motion: reduce`; el visitante todavía puede iniciarlo manualmente. Es una precaución relevante para animaciones con escala y paneo.

## Escaleta

| Tiempo | Acción |
|---|---|
| 00.00–01.28 s | Entrada del afiche desde sombra, inclinación 3D leve y settle. |
| 01.28–02.72 s | Push-in hacia los ojos del tatuaje. |
| 02.72–04.18 s | Recorrido y lectura del tramo de 35 %. |
| 04.18–05.46 s | Pan hacia el beneficio de 20 %. |
| 05.46–06.72 s | Pan al 10 % y al recuadro de cupos limitados. |
| 06.72–10.00 s | Pull-back, afiche completo, reflejo dorado y cierre. |

## Habilidades que ayudan a dominar esta técnica

1. **Dirección de arte y composición:** jerarquía visual, contraste, zonas seguras y balance entre texto e imagen.
2. **Máscaras / rotoscopia / inpainting:** separar el sujeto con bordes limpios y reconstruir el fondo que aparece detrás al mover la cámara.
3. **Cámara y profundidad:** perspectiva, distancia focal, capas Z, parallax y control de distorsión.
4. **Animación:** keyframes, timing, spacing, curvas de easing, staging y acciones secundarias.
5. **Composición y luz:** sombras, viñeta, reflejos, integración de capas y gradación de color.
6. **Entrega audiovisual:** relación de aspecto, zonas seguras para redes, H.264, BT.709, bitrate y control de calidad.
7. **Accesibilidad:** pausa, controles claros y respeto a la preferencia de movimiento reducido en la vista web.

## Revisión de contenido antes de publicar

La pieza final ya muestra **«cotizaciones ya hechas»**; los porcentajes y los montos no se modificaron. El JPEG enviado se conserva aparte. Confirma que los descuentos, montos mínimos y cupos siguen vigentes antes de difundir la oferta.

## Regenerar el MP4

Desde la raíz del repositorio:

```bash
python -m venv .venv
.venv/bin/python -m pip install numpy pillow opencv-python-headless imageio-ffmpeg
.venv/bin/python scripts/correct_promo_copy.py
.venv/bin/python scripts/build_promo_motion.py
```

Primero se corrige el copy sobre el afiche original y se guarda el PNG sin recompresión JPEG; después se renderiza la animación a 60 fps. `ffmpeg` (incluido por `imageio-ffmpeg`) codifica el MP4 H.264 de alta calidad.

## Fuentes consultadas

- Adobe, [Animate photos with a parallax effect](https://helpx.adobe.com/ph_fil/after-effects/how-to/animate-picture.html) — separación de planos, profundidad Z y cámara virtual.
- Adobe, [The complete guide to animation easing](https://www.adobe.com/uk/creativecloud/animation/discover/easing.html) — keyframes y aceleración/desaceleración.
- Adobe, [The essential principles of animation](https://www.adobe.com/in/creativecloud/roc/blog/video/animation-principles.html) — staging, timing, slow in/slow out y acción secundaria.
- MDN, [The `prefers-reduced-motion` CSS media feature](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/@media/prefers-reduced-motion) — respetar la preferencia del usuario en la página de vista previa.
