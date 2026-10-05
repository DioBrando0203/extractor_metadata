# Arquitectura del backend

## Alcance

Inspector MSG local Linux/Windows, sin BD/login/usuarios registrados/telemetría/historial.
Entrada multipart por archivo; salida JSON de metadatos. Archivos originales inalterados.
Leer también `REQUERIMIENTOS.md` para cobertura y pendientes.

## Árbol real

```text
app/
  main.py                         API, CORS/origen local, host local y build frontend
  api/router.py                   reúne rutas /api
  api/routes/health.py            disponibilidad, almacenamiento none
  api/routes/messages.py          recepción streaming, validación, temporal, threadpool
  core/config.py                  límites y orígenes de loopback
  core/middleware.py              tamaño total antes de multipart y control Origin
  core/errors.py                  errores seguros con código
  models/schemas.py               MetadataItem, AttachmentMetadata, MessageMetadata, respuesta
  services/worker.py              proceso spawn, timeout, memoria Linux, JSON por pipe
  services/message_extractor.py   firma CFB, propiedades OLE/MAPI, parser y recuperación
  services/file_metadata.py       registro por firma, extractores nativos + ExifTool
  services/body_text.py           texto legible desde HTML sin recursos activos
tests/
  msg_factory.py                  generador CFB v4 sintético propio (sin correos reales)
  test_messages.py                contrato HTTP, limpieza, corruptos, adjuntos grandes, rutas
  test_worker.py                  timeout y diagnóstico de fallo
  test_file_metadata.py           formatos reales sintéticos y ExifTool
  test_health.py                  disponibilidad local
  test_encoding.py                MSG ANSI y codepage japonesa
  test_body_text.py               HTML convertido sin scripts/recursos externos
```

## Flujo

HTTP POST → middleware límite/origen → multipart → copia `input.msg` dentro de TemporaryDirectory →
threadpool → proceso spawn → validación OLE → streams MAPI acotados → extract-msg →
cada adjunto por registro → JSON acotado por pipe → respuesta → cierre UploadFile y eliminación del temporal.

El trabajo pesado no corre en el event loop. El proceso termina al exceder timeout o finalizar.
En Linux se aplica RLIMIT_AS; Windows conserva timeout y límites de bytes (sin límite de memoria OS).
Las librerías pueden necesitar materializar un adjunto en RAM; el proceso evita comprometer la API.
La limpieza aplica a terminación normal, errores y timeout; un corte del sistema/SIGKILL puede dejar
temporales del SO. No afirmar garantía de borrado tras apagado abrupto.

## Contrato

- `GET /api/health`: `{"status":"ok","storage":"none"}`.
- `POST /api/messages/extract`: campo multipart `file`, un .msg.
- Respuesta: `message` y `processed_locally=true`.
- Mensaje: file_name, file_size_bytes, subject, sender, recipients, sent_at, received_at,
  body_preview, body_truncated, status (complete|partial), headers[], properties[], attachments[], warnings[].
- Item: group/label/value, todos strings. Adjunto: nombre, MIME, tamaño, metadata[] y warnings[].
- Error: HTTP 415 (tipo), 413 (tamaño), 422 (lectura), 403 (origen); detail seguro y código donde aplica.
- Sin jobs, IDs persistentes, sesiones, descarga de binarios ni caché de resultados.
- Frontend build: `GET /` y `/assets/*`, montados sólo si existe `frontend/dist` al arrancar.

## Límites

100 MB MSG; 50 MB/adjunto profundo; 150 MB adjuntos acumulados; 200 adjuntos;
100.000 caracteres de cuerpo; 8.000 por valor; 1.000 propiedades por extractor;
3.000.000 caracteres de metadata por respuesta; 90 s de worker; 1 GiB de memoria virtual Linux;
dos análisis simultáneos en la API (límite de procesos, no de usuarios).
Adjuntos >10 MB son advertidos y procesados dentro de los límites.
Límites generales viven en config.py; presupuestos ZIP/ExifTool en file_metadata.py.
El presupuesto global externo se define al coordinar adjuntos en message_extractor.py.
Cualquier cambio debe actualizar esta arquitectura.

## Extractores

Firma antes de extensión para imágenes/PDF/ZIP/OLE. Imagen mediante Pillow; PDF mediante pypdf.
OOXML mediante ZIP/XML acotado, sin cargar hojas completas ni ejecutar macros. Se inspeccionan
miembros, tamaño descomprimido y ratio; archivos sospechosos producen resultados parciales.
DXF ASCII mediante ezdxf; DWG sólo cabecera ACxxxx. Los formatos desconocidos conservan metadata genérica.
ExifTool opcional: argumentos constantes sólo lectura, stdin, sin shell, timeout y stdout máximo 1 MiB.
El presupuesto externo global por MSG es 30 segundos; luego se conservan los extractores nativos.
Complementa la lectura
nativa; sus errores no bloquean el correo. DWG no figura en la lista oficial de soporte de ExifTool.

## Recuperación y seguridad

Si falla extract-msg pero hay streams de texto, devolver status partial con recuperación OLE y aviso.
Si un atributo/stream/adjunto falla, conservar el resto. No forzar UTF-8 en MSG ANSI:
se usa la codepage 0x3FFD para la recuperación y el parser detecta la original.
Preflight OLE comprueba tamaño del adjunto antes de inicializarlo; se procesa y libera uno por uno.
Si falta la fecha primaria, se intenta Date del encabezado. Si falta texto, se convierte HTML a texto.
El navegador oculta la ruta local, así que sólo se pueden diagnosticar caracteres y longitud del nombre.
No ejecutar macros ni HTML; cuerpo en texto, binarios resumidos por tamaño.
Host/Origin locales ayudan a impedir que una página externa invoque el servicio.
Arranque loopback y sin access-log. No publicar el servicio ni compartir correos en tests/logs.

## Verificación y continuidad

Desde backend: `.venv/bin/python -m pytest`, `.venv/bin/ruff check app tests`,
`.venv/bin/ruff format --check app tests`. Windows usa Scripts/python.exe.
Instalación y lanzador en README raíz. Estado de pruebas en `calidad/RESULTADOS.md`.
Actualizar arquitectura, reglas aplicables, bloqueos y bitácora con fecha/hora America/Lima.
Pendientes: MSG anidado/objetos embebidos, DWG profundo, corpus autorizado de corrupción y prueba Windows.
