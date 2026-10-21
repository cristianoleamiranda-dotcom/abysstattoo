---
name: abyss-video-image-studio
description: Suite activa de edición profesional de imagen y video comercial (PhotoCraft + LightCraft + VectorCraft + FilmCraft + Remotion Reels Best Practices) para Abyss Tattoo Studio. Úsala para curar activos crudos, limpiar capturas/bordes, aplicar etalonaje colorimétrico LAB, componer gráficos vectoriales HUD y masterizar Reels comerciales 9:16 (1080x1920 @ 60fps / 30fps) con escala de planos, tiros de cámara, zooms ópticos, diseño sonoro y CTA de conversión.
---

# Abyss Video & Image Studio — Active Skill Suite

## 1. Módulos Activos Integrados

1. **`photocraft` (Curaduría, Reencuadre & Restauración Óptica)**:
   - Auditoría previa obligatoria de todo activo crudo antes de entrar a línea de tiempo: descartar o reencuadrar capturas con interfaz móvil (barras de estado/Instagram), eliminar textos promocionales obsoletos quemados en bordes, descartar miniaturas `< 100 KB` con macrobloques y reescalar mediante interpolación `Lanczos-4` + máscara de enfoque adaptativa (`Unsharp Mask`).
2. **`lightcraft` (Etalonaje Colorimétrico & Tone-Mapping BT.709)**:
   - Conversión de clips HDR HLG (`bt2020nc / arib-std-b67` 10-bit) a curva estándar `BT.709` (`yuv420p`) sin sobreexposición de altas luces.
   - Revelado unificado en espacio perceptual `CIE LAB` (`CLAHE clipLimit=1.7`) + *Split-Toning* de identidad Abyss: sombras profundas en **Obsidiana/Negro (`#14100D` / `#1E1B18`)**, medios tonos cálidos en **Hueso (`#B5A295` / `#C6B7AB`)**, altas luces en **Crema Editorial (`#EAE3DD` / `#F6F1ED`)** y acento mineral en **Verde Salvia / Teal (`#556C65` / `#6C928A`)**.
3. **`vectorcraft` (Identidad Gráfica, HUD Óptico & Tipografía Variable)**:
   - Instanciación de pesos estáticos reales desde fuentes variables oficiales (`Cinzel` 600–800 para titulares clásicos y `Montserrat` 500–800 para UI técnica y CTA).
   - Visor cinematográfico (`┌ ┐ └ ┘`, indicador `● REC`, distancia focal, clasificación de plano, líneas de llamada `•───╲____`, emblema circular oficial y pastilla CTA de alto contraste).
   - **Zona Segura Estricta 9:16 (`1080×1920`)**: Todo texto crítico y CTA dentro de `x ∈ [84, 920]`, `y ∈ [220, 1560]` para evitar solapamiento con iconos laterales y descripción inferior de Instagram Reels / TikTok / Meta Ads.
4. **`filmcraft` + `remotion-best-practices` (Dirección Cinematográfica & Audio Master)**:
   - Estructura comercial de 15.00 segundos sincronizada a pulso musical (`120 BPM`, `1 beat = 0.50s = 30 frames @ 60fps`):
     - `0.00s – 2.50s` **Hook**: Interrupción visual en movimiento desde el frame `0` + promesa de valor inmediata.
     - `2.50s – 7.50s` **Contexto & Autoridad en Vivo**: Progresión de planos (Cenital → Crash Zoom → Macro Aguja ECU → Travelling Gimbal → Plano Americano en Cabina Seremi).
     - `7.50s – 11.50s` **Payoff de Portafolio**: Montaje rápido al golpe del bombo con contraste de direcciones, zooms y pantalla dividida dual (*Split-Screen*).
     - `11.50s – 15.00s` **Cierre & CTA Accionable**: Lockup de marca + llamado a la acción único y directo (WhatsApp, dirección verificada y usuario) + loop invisible hacia el frame `0`.
   - Curvas físicas no lineales (`easeInQuad`, `easeOutQuart`, `easeInOutCubic`, `spring`) + *Directional / Radial Motion Blur* en transiciones rápidas + masterización de audio estéreo `48 kHz` con foley y compresión suave.
