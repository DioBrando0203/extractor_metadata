# Plan de calidad (backend)

Reglas en `reglas_calidad/REGLAS.md`. Última ejecución en `RESULTADOS.md`.

## Mapa de pruebas

- `tests/msg_factory.py`: genera MSG CFB v4 sintéticos con asunto, remitente, cuerpo y un adjunto.
- `test_messages.py`: rutas HTTP, limpieza de temporales, recuperación FAT y OLE, presupuestos, origen y host, adjuntos grandes, descarga.
- `test_previews.py`: miniaturas de imágenes, DWG (PNG y BMP), DXF y Office; formatos rechazados; presupuesto; endpoint `preview=true`.
- `test_inline_recovery.py`: RTF suelto (válido, corrupto, incoherente), etiquetas `<img>`, emparejamiento por tamaño y proporción, ambigüedad y MSG dañado completo.
- `test_envelope.py`: sobre desde encabezados de transporte y propiedades alternativas, cadena de respaldo, imágenes `cid:` como marcadores y Content-ID.
- `test_file_metadata.py`: extractores por formato (imagen, PDF, Office, DXF, DWG) e integración segura con ExifTool simulado.
- `test_worker.py`: timeout del hijo, plazo proporcional y diagnóstico seguro.
- `test_encoding.py`: páginas de códigos ANSI.
- `test_body_text.py`: HTML a texto sin scripts ni recursos remotos.
- `test_health.py`: salud local sin estado.
- `test_embedded.py`: correos adjuntos (lectura, anidamiento, límites, parser caído, stream dañado, descarga como `.msg` y con `message_path`) y adjuntos por referencia (nube, ruta, sin dirección).
- `test_config.py`: listas de Host y Origin desde el entorno (modo LAN, ADR-B12) y valores de loopback por defecto.

## Comandos

Desde `backend/`:

- `.venv/Scripts/python.exe -m pytest` (Linux: `.venv/bin/python`).
- `.venv/Scripts/python.exe -m ruff check app tests`.
- `.venv/Scripts/python.exe -m ruff format --check app tests`.

## Cuándo ampliar

- Formato nuevo: prueba válida y corrupta (QB-03).
- Cambio en worker o límites: repetir timeout y MSG grande (QB-08).
- Cambio de contrato: E2E del frontend (`npm run test:e2e`) con el backend reiniciado.
- Refactorización: suite completa sin tocar aserciones (QB-07).

## Revisión manual

- Con un MSG real del usuario: sólo local, nunca se copia al repositorio; registrar resultados sin nombres ni contenido.
- Confirmar que `temp_root` queda vacío tras análisis, descarga y vista previa.
