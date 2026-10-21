---
name: abyss-video-image-studio
description: >
  Suite integrada de edición profesional de video, imagen, color, tipografía cinética y sonido publicitario
  para Abyss Tattoo Studio (José Joaquín Pérez 528, San Bernardo). Aplica auditoría y curaduría previa al montaje,
  conversión HDR HLG 10-bit -> BT.709, rig de cámara virtual 3D sub-píxel (zooms ópticos, tiros de cámara,
  perspectiva 3D, speed ramps, whip pans), tipografía editorial en zonas seguras 9:16 y masterización H.264 + AAC 48 kHz.
---

# Abyss Video & Image Studio — Skill Activa

Implementación ejecutable del ecosistema audiovisual de **Abyss Tattoo Studio** en `/home/user/abysstattoo/scripts/`.

## Módulos activos y scripts ejecutables

| Módulo | Script | Función principal |
|---|---|---|
| **PhotoCraft & LightCraft** | `scripts/prepare_commercial_assets.py` | Auditoría y filtrado previo al montaje; descarte de promos antiguas (`20% / 10% / $70.000`) y dirección errónea (`548`); recorte limpio 9:16 + overscan +20 % (`1296×2304`); conversión HDR HLG 10-bit (`bt2020nc / arib-std-b67`) -> `BT.709` SDR; etalonaje LAB CLAHE + split-toning Obsidiana/Salvia/Hueso; extracción radial sub-píxel del emblema circular con canal alfa. |
| **Audit Proof** | `scripts/build_audit_sheet.py` | Lámina comparativa Antes vs. Después (`film/auditoria_edicion_material_reel.jpg`) documentando recorte de rótulos quemados, corrección de numeración oficial (`528`), descarte de promociones caducadas y tone-mapping HDR. |
| **VectorCraft & Virtual Rig 3D** | `scripts/reel_kit.py` | Rig de cámara virtual proyectiva 3×3 sub-píxel (`cv2.warpPerspective`: *crash zoom*, *push-in*, *pull-out*, *dolly*, inclinación 3D *pitch/yaw*, *Dutch roll*, vibración orgánica de cámara en mano, *whip-pan shutter blur* y *radial zoom blur*); tipografía con `ink-bbox` real, pastillas CTA con centrado óptico sub-píxel y barrido especular (*shimmer*), y visor HUD estilo Solen (`┌ ┐ └ ┘`, `•───`). |
| **SoundCraft** | `scripts/build_reel_audio.py` | Mezcla publicitaria estéreo 48 kHz sincronizada a 100 BPM exactos (`0.60 s/negra`): cama musical oficial con *sidechain ducking*, foley de máquina rotativa en macros de aguja, ráfaga aérea FPV en vuelo de dron, obturadores en cortes rápidos, *riser* de tensión, *sub-bass drop* y campana cristalina en el CTA. |
| **FilmCraft Master** | `scripts/build_reel_commercial.py` + `scripts/build_storyboard.py` | Montaje de 12 planos cinematográficos en **15.00 s exactos (900 frames @ 60 fps)**, masterización `1080×1920` H.264 High Level 4.2 (`BT.709`, `+faststart`, `AAC 192 kbps`), derivada web `30 fps`, portadas `cover_hook.jpg` / `poster_cta.jpg` y storyboard completo (`storyboard_reel_abyss_15s.jpg`). |

## Reglas editoriales e identidad invariables

1. **Dirección oficial verificada**: **José Joaquín Pérez 528, San Bernardo · Santiago** (jamás usar la numeración antigua `548`).
2. **Prohibición de promociones pasadas**: cero menciones a `20% dcto`, `10% adicional`, `$70.000 CLP`, `2x1` ni campañas temporales vencidas.
3. **Curaduría previa obligatoria**: auditar resolución, códec, rango dinámico e interfaces quemadas **antes** de incorporar cualquier activo a la línea de tiempo.
4. **Zonas seguras 9:16 (Instagram Reels / TikTok / Meta Ads)**: textos y CTA estrictamente contenidos en `x ∈ [84, 960]`, `y ∈ [210, 1500]`, dejando el tercio superior/central despejado para lucir el arte y los tatuajes sin obstrucción.
5. **Paleta cromática oficial**: Obsidiana `#14100D`, Panel `#1A1512`, Hueso `#B5A295`, Crema `#EAE3DD`, Papel `#F6F1ED`, Verde Salvia `#556C65` y Teal Claro `#9EC4BA`.
