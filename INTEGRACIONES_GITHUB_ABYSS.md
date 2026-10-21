# Integraciones de GitHub aplicadas a `abysstattoo`

A partir de los mecanismos oficiales de integración de GitHub (**GitHub Actions**, **Acciones Personalizadas**, **API REST / GraphQL** y **GitHub Apps / Webhooks**), este repositorio cuenta ahora con su propia **arquitectura de integración automatizada activa**.

---

## 1. Mapa de tipos de integración en GitHub y su rol práctico

| Tipo de integración | Cuándo usarla | Implementación en `cristianoleamiranda-dotcom/abysstattoo` |
|---|---|---|
| **Flujos de trabajo de GitHub Actions** (`.github/workflows/*.yml`) | Automatizar validaciones, builds, reportes y despliegues ante eventos del repositorio (`push`, `pull_request`, `workflow_dispatch`). | **Implementado y activo**: `.github/workflows/abyss-ci-and-pr-report.yml` se ejecuta automáticamente en cada `push` y `pull_request`. |
| **Acciones personalizadas (Custom Composite Actions)** (`.github/actions/*/action.yml`) | Encapsular pasos reutilizables de inspección técnica para mantener los flujos limpios y modulares. | **Implementado y activo**: `.github/actions/abyss-media-audit/action.yml` instala `ffprobe` y ejecuta `scripts/ci_audit_deliverables.py`. |
| **API REST y GraphQL de GitHub** (`actions/github-script` / `gh api`) | Leer PRs abiertos, publicar o actualizar comentarios automáticos con tablas de control de calidad, gestionar issues o consultar estados de Pages. | **Implementado y activo**: el job localiza el Pull Request asociado a la rama y crea/actualiza un comentario único (`issues.createComment` / `issues.updateComment`) con el informe completo de `ffprobe` y auditoría de marca. |
| **GitHub Pages / Apps de despliegue** (GitHub Pages / Vercel GitHub App) | Publicar automáticamente el sitio estático y la sala `reel.html` cada vez que un PR se fusiona en `main`. | **Configurado en el repositorio**: GitHub Pages sirve `main` en `https://cristianoleamiranda-dotcom.github.io/abysstattoo/` (y al fusionar el PR publica también `/reel.html` y todos los másters de `film/`). |

---

## 2. Qué verifica automáticamente la integración en cada cambio

1. **Integridad invariable de marca y ubicación**:
   - Exige la presencia de la dirección oficial **José Joaquín Pérez 528** en `index.html` y `reel.html`.
   - Bloquea automáticamente cualquier regresión de la numeración antigua `548` o promociones obsoletas (`20% dcto`, `$70.000`).
   - Verifica que el **100 %** de los enlaces locales (`src`, `href`, `poster`) existan en disco sin rutas rotas.
2. **Inspección broadcast / social de los 4 másters MP4 (`ffprobe`)**:
   - Comprueba resolución exacta (`1080×1920` en `9:16` y `1080×1350` en `4:5`), framerate (`60 fps` / `30 fps`), duración exacta (`15.00 s`), matriz de color `BT.709` y pista de audio estéreo a `48 000 Hz`.
3. **Reporte automático en el Pull Request**:
   - Publica (y en futuros commits actualiza sin duplicar) un comentario en el PR con el resumen ejecutivo y la tabla técnica completa.
