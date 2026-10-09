# Plan de calidad (backend)

Reglas en `reglas_calidad/REGLAS.md`. Última ejecución en `RESULTADOS.md`.

## Mapa de pruebas

- `tests/msg_factory.py`: genera MSG CFB v4 sintéticos con asunto, remitente, cuerpo, un adjunto, clase de mensaje, propiedades con nombre, correos adjuntos y referencias.
- `tests/generar_ejemplos.py`: escribe en una carpeta los 8 MSG de ejemplo de la guía del README para revisión manual (no es una prueba).
- `test_messages.py`: rutas HTTP, limpieza de temporales, recuperación FAT y OLE, presupuestos, origen y host, adjuntos grandes, descarga.
- `test_previews.py`: miniaturas de imágenes, DWG (PNG y BMP), DXF y Office; formatos rechazados; presupuesto; endpoint `preview=true`.
- `test_inline_recovery.py`: RTF suelto (válido, corrupto, incoherente), etiquetas `<img>`, emparejamiento por tamaño y proporción, ambigüedad y MSG dañado completo.
- `test_envelope.py`: sobre desde encabezados de transporte y propiedades alternativas, cadena de respaldo, imágenes `cid:` como marcadores y Content-ID.
- `test_file_metadata.py`: extractores por formato (imagen, PDF, Office, DXF, DWG) e integración segura con ExifTool simulado.
- `test_worker.py`: timeout del hijo, plazo proporcional y diagnóstico seguro.
- `test_encoding.py`: páginas de códigos ANSI.
- `test_body_text.py`: HTML a texto sin scripts ni recursos remotos; destino visible de los enlaces web.
- `test_health.py`: salud local sin estado.
- `test_embedded.py`: correos adjuntos (lectura, anidamiento, límites, parser caído, stream dañado, descarga como `.msg` y con `message_path`) y adjuntos por referencia (nube, ruta, sin dirección).
- `test_eml.py`: `.eml` adjunto (sobre, cuerpo con imagen en posición, adjuntos, correo dentro), descargas por `message_path` dentro del EML, `.msg` adjunto como archivo y archivos que sólo lo parecen.
- `test_raw_recovery.py`: formatos sueltos (JPEG, GIF, ZIP/Office, PDF con su cierre), truncados, anidados, sectores y mini sectores legibles, activación con el parser caído y descarga del suelto.
- `test_rescue.py`: firma borrada repuesta en copia; cabecera destruida con sobre, adjuntos y descarga por HTTP.
- `test_minifat_recovery.py`: MiniFAT borrada de la cabecera con el mini stream en orden inverso (`build_cfb(scatter=True)`): asunto, nombre, Content-ID y descarga; tabla incoherente, tablas ambiguas y cabecera sana sin copia.
- `test_item_details.py`: convocatoria, respuesta, contacto, tarea y correo sin elemento, con propiedades con nombre sintéticas.
- `test_smime.py`: firmado en claro (contenido, adjuntos, descarga, parser caído), opaco, cifrado, con permisos IRM y correo normal.
- `test_archive.py`: ZIP con todos los adjuntos (sin enlaces, nombres repetidos numerados, correo adjunto por `message_path`, sin nada descargable) y nombre de descarga legible entre orígenes.
- `test_config.py`: listas de Host y Origin desde el entorno (modo LAN, ADR-B12) y valores de loopback por defecto.

## Comandos

Desde `backend/`:

- `.venv/Scripts/python.exe -m pytest` (Linux: `.venv/bin/python`).
- `.venv/Scripts/python.exe -m ruff check app tests`.
- `.venv/Scripts/python.exe -m ruff format --check app tests`.
- Linux sin instalar nada en el equipo (PEN-10): contenedor `python:3.12-slim` con `backend/` montado en sólo lectura y copiado dentro; `pip install -c requirements.lock -e ".[dev]"` y luego los tres comandos anteriores con `python`.

## Cuándo ampliar

- Formato nuevo: prueba válida y corrupta (QB-03).
- Cambio en worker o límites: repetir timeout y MSG grande (QB-08).
- Cambio de contrato: E2E del frontend (`npm run test:e2e`) con el backend reiniciado.
- Refactorización: suite completa sin tocar aserciones (QB-07).

## Revisión manual

- Con un MSG real del usuario: sólo local, nunca se copia al repositorio; registrar resultados sin nombres ni contenido.
- Confirmar que `temp_root` queda vacío tras análisis, descarga y vista previa.
