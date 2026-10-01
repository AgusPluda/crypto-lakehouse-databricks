# Cómo regenerar los diagramas

1. `python build_all.py` genera los cuatro `.excalidraw` en `docs/diagrams/` (paleta y estilo en `dl.py`).
2. Para exportar a PNG con el motor real de Excalidraw (tipografía Virgil incluida):
   copiá los `.excalidraw` y `export_png.html` en una carpeta, levantá `python export_server.py <carpeta_salida>`
   (sirve en el puerto 8765 y recibe los PNG), abrí `http://localhost:8765/export_png.html` y esperá a que diga `LISTO`.
   La página carga `@excalidraw/excalidraw` desde esm.sh, así que necesita internet.
