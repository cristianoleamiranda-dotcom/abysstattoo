# Dropbox source manifest — A VISTA / BLACK

This manifest records the original source material identified in the user's Dropbox folder. The originals remain in Dropbox and have not been moved, renamed, or modified.

## Approved poster reference

- **02 — CORTE** (approved low-resolution direction, 1080 × 1350):  
  https://www.dropbox.com/preview/ABYSS_BLACK_2026/REVISION_ARTE_02/02_CORTE_1080x1350.jpg
- **Revision 02 comparison sheet**:  
  https://www.dropbox.com/preview/ABYSS_BLACK_2026/REVISION_ARTE_02/comparativa_3_direcciones.jpg

The approved CORTE image is a layout reference/proof. It is not to be mistaken for the final high-resolution poster or the original source photograph.

## Original source archive

- **Technical asset kit**: `/ABYSS_BLACK_2026/ABYSS_BLACK_kit_tecnico.zip` (4,399,068 bytes; Dropbox item ID `id:R5R3JUuvUCsAAAAAAAAB0Q`)  
  https://www.dropbox.com/preview/ABYSS_BLACK_2026/ABYSS_BLACK_kit_tecnico.zip

The archive is the source package for the original materials, including the poster engine and processed real-photo assets documented in `MEMORIA_PROYECTO.md`. Extract the approved real image and original emblem from this archive before rendering the final poster.

## Related campaign references (not poster source images)

- 12-shot storyboard:  
  https://www.dropbox.com/preview/ABYSS_BLACK_2026/storyboard_abyss_black_12planos.jpg
- Project production memory: `/ABYSS_BLACK_2026/MEMORIA_PROYECTO.md`
- D01 SIGNAL feed master (separate campaign piece; do not use as the CORTE poster source):  
  https://www.dropbox.com/preview/ABYSS_BLACK_2026/01_PARA_PUBLICAR/AV_BLACK_D01_SIGNAL_feed_master_2160x2700.png

## Transfer status

The GitHub connector available in this workflow supports UTF-8 text file creation and updates, but does not expose a binary-file upload operation for arbitrary Dropbox files. Therefore, this commit records the exact original Dropbox source locations and approved references; it does **not** claim that the ZIP, JPG, or PNG binaries have been copied into GitHub.

To complete a byte-for-byte import, use GitHub's web upload or a Git client with the Dropbox originals. Keep the imported files under this isolated branch only, preferably:
- `assets/source/02_CORTE_approved_reference.jpg`
- `assets/source/ABYSS_BLACK_kit_tecnico.zip`
- extracted approved source image and emblem under `assets/footage/` and `assets/brand/`

Do not substitute the D01 SIGNAL artwork for the CORTE source photo.
