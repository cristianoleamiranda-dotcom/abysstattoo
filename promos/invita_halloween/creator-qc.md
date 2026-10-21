# QA técnico y editorial · CapCut Creator

## Gate técnico reproducible

Comando:

```bash
python3 scripts/audit_creator_assets.py --profile creator-vertical \
  promos/invita_halloween/invita_halloween_pro_master_1080x1920_60fps.mp4 \
  promos/invita_halloween/invita_halloween_abyss_edition_1080x1920_60fps.mp4
```

Resultado ejecutado localmente:

| Archivo | Resolución | FPS | Duración | Audio | Gate técnico |
|---|---:|---:|---:|---|---|
| `invita_halloween_pro_master_1080x1920_60fps.mp4` | 1080×1920 | 60.000 | 16.00 s | Sí | PASS |
| `invita_halloween_abyss_edition_1080x1920_60fps.mp4` | 1080×1920 | 60.000 | 16.00 s | Sí | PASS |

El validador confirma solo metadatos y decodificación inicial. **No** certifica la revisión de CapCut, derechos musicales, elegibilidad FYF, seguridad visual, legibilidad, funcionamiento del borrador en una versión instalada de CapCut ni puntos de creador.

## Revisión manual aplicada a la pieza de invitación

- 6 escenas, pantalla de datos dedicada `7.50–11.20 s` y CTA final; las etiquetas/hashtags y los requisitos exactos de campaña deben verificarse contra la misión activa al momento de publicar.
- Las escenas limpias están separadas para permitir texto reemplazable; el borrador del ZIP requiere abrirse en la versión de CapCut del usuario para confirmar la editabilidad y el render final.
- Audio synth original generado por el proyecto; conservarlo como pista propia, aunque la disponibilidad/licencia para usar audio en plantillas puede variar según el destino y la región. Verificarlo en la biblioteca/categoría autorizada de CapCut.
- Las imágenes son de invitación Halloween estilizada sin franquicias reconocibles; la revisión final de moderación siempre corresponde a CapCut.

## Archivos del usuario pendientes de revisión

Los 15 enlaces `tmpfiles.org` compartidos en el chat no se procesaron aquí. No están descargados en el repositorio y son enlaces temporales; no se debe afirmar un análisis visual o técnico de ellos. Para auditar esos originales, vuelve a adjuntarlos en el chat o envía enlaces directos estables (por ejemplo, Dropbox con descarga habilitada) y ejecuta el validador sobre los archivos locales. Cada archivo requiere además revisión visual y de derechos manual.
