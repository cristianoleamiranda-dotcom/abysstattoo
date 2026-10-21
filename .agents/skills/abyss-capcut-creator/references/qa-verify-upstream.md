# SKILL · QA y verificación dura
1. Ningún cambio se anuncia sin curl de producción: tag BUILD, contadores de marcadores (clases nuevas, data-*), HTTP 200 de cada asset crítico.
2. Parse check de JS antes del push (vm.SourceTextModule) + grep de bare imports ('from gsap/lenis') en sitios sin bundler.
3. Rescates git: fetch + reset --hard FETCH_HEAD + re-aplicar ediciones con asserts; binarios a /tmp antes de rebase; NUNCA force-push.
4. CI: html-validate + LHCI (a11y ≥.85 error, perf warn) en cada push; leer logs del job por API.
5. Cache del usuario: entregar siempre URL con parámetro fresco (?v=N) y decir qué tag BUILD mirar; si el tag no coincide → es cache, no el sitio.
6. Deuda: lo que no se cumple se documenta con estado y plan (perf headless), no se oculta.
