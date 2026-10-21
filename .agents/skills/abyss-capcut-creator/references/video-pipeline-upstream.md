# SKILL · Pipeline de video/imagen (ffmpeg)
1. Backbone scrub: GOP corto obligatorio (-g 8 -keyint_min 8 -sc_threshold 0) + faststart.
2. Peso objetivo: backbone ≤3 MB (1080×1620 crf22 slow); loops ≤1.5 MB (960×540 crf26); Ken Burns desde foto real zoompan d=125 fps25.
3. Fotos web: scale 'min(1600,iw)':-2 -q:v 5; derivados únicos por crop+eq (brillo/sat) — nunca repetir la misma imagen en dos productos.
4. Verificar SIEMPRE con probe: tamaño, duración, resolución antes del push.
5. Videos secundarios: muted loop playsinline preload=metadata + play/pause por IntersectionObserver.
