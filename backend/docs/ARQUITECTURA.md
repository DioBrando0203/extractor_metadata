# Arquitectura del backend

Servicio local que abre MSG, devuelve lo legible y entrega adjuntos y vistas previas bajo demanda. Decisiones y motivos en `decisiones/ADR.md`.

## Capas

```text
api/routes        HTTP: valida, copia a temporal, delega, responde y limpia
services/worker   proceso hijo aislado con plazo y respuesta JSON
services/msg      lectura del contenedor MSG (parser + recuperación OLE)
services/metadata metadatos por formato (Strategy)
services/previews miniaturas y vistas previas JPEG
models, core      contrato Pydantic, configuración, errores, middleware
```

Dependencias permitidas, siempre hacia abajo:

- `api` importa `services.worker`, `models`, `core`. Nunca `msg`, `metadata` ni `previews`.
- `worker` importa `msg` y `previews` dentro del proceso hijo.
- `msg` importa `metadata`, `previews`, `models`, `core`, `body_text`.
- `metadata` importa `previews.embedded`, `models`, `core`.
- `previews` importa sólo `core`.
- `models` y `core` no importan servicios.
- Prohibido el import circular; si aparece, extraer lo común a un módulo inferior.

## Paquetes y módulos

```text
app/
  main.py                      API local y build del frontend en "/"
  api/routes/messages.py       POST /extract y POST /attachment
  api/routes/health.py         GET /health
  core/config.py               Settings inmutables: límites y presupuestos
  core/errors.py               ExtractionError con código seguro
  core/middleware.py           Host y Origin locales
  models/schemas.py            MessageMetadata, AttachmentMetadata, MetadataItem
  services/worker.py           _run_isolated: spawn, plazo, JSON, limpieza del hijo
  services/body_text.py        HTML a texto sin ejecutar ni resolver recursos
  services/msg/
    __init__.py                API: extract_msg_file, extract_attachment_file
    reader.py                  orquesta: parser MSG o recuperación OLE (_ReadContext)
    parsed_fields.py           lectura aislada de cada campo del parser (cuerpo, fechas, encabezados)
    envelope.py                sobre de respaldo: propiedades MAPI alternativas y encabezados de transporte
    ole_reader.py              OleMetadata: propiedades MAPI, adjuntos (OleAttachment con Content-ID), página de códigos
    attachments.py             adjuntos desde el parser o desde OLE
    raw_recovery.py            PNG/PDF completos fuera de enlaces OLE
    fat_recovery.py            DIFAT truncada reparada en copia temporal
    download.py                copia un adjunto al temporal de la solicitud
    limits.py                  presupuesto de miniaturas y metadatos
    names.py                   avisos y nombres seguros
    text.py                    valores a texto acotado
  services/metadata/
    __init__.py                API: extract_file_metadata
    extractor.py               registro NATIVE_EXTRACTORS y combinación de resultados
    detection.py               formato por firma
    results.py                 ExtractionResult, add_item, limited
    image.py pdf.py office.py cad.py exiftool.py
  services/previews/
    __init__.py                API: render_preview, thumbnail_data_uri, write_large_preview, embedded_thumbnail
    embedded.py                miniatura guardada en DWG, DXF y Office
    render.py                  JPEG acotado con lista cerrada de formatos
```

## Flujo de análisis

1. `POST /api/messages/extract` recibe multipart `file` con extensión `.msg`.
2. La ruta copia por bloques a `temp_root/analysis-*/input.msg` y toma un cupo de `extraction_slots`.
3. `run_extraction` lanza `_worker` en un hijo `spawn`; el plazo crece con el tamaño (`_timeout_for_size`).
4. `extract_msg_file` valida firma OLE, aplica `recovered_ole_path` y lee `OleMetadata`.
5. Estrategia principal: `extract_msg.openMsg`. Si falla y hay asunto, cuerpo, remitente o encabezados de transporte en OLE, estrategia de recuperación.
6. En ambas estrategias, los campos del sobre vacíos se completan con `Envelope.complete_with`: primero propiedades MAPI alternativas, luego encabezados de transporte (`007D`), que viven en sectores normales y resisten daños del mini stream.
7. Cuerpo: texto plano; si no marca imágenes incrustadas pero el HTML sí, se usa el HTML convertido, que conserva cada `<img src="cid:…">` como marcador `[cid:…]` en su posición.
8. Cada adjunto pasa por `attachment_from_payload`: metadatos por formato y miniatura si queda presupuesto de tiempo.
9. `limit_response` acota miniaturas (`max_total_preview_chars`) y metadatos (`max_total_metadata_chars`).
10. El hijo envía JSON; el padre valida con Pydantic y borra el temporal.

## Flujo de adjunto

1. `POST /api/messages/attachment` recibe `file`, `attachment_index` y opcional `preview`.
2. `run_attachment_extraction` ejecuta `_attachment_worker`: `extract_attachment_file` copia el adjunto a `download-*/attachment.bin`.
3. Con `preview=true`, `write_large_preview` lo sustituye por un JPEG de hasta 2048 px o responde `NO_PREVIEW`.
4. `FileResponse` entrega el archivo y una tarea de fondo borra el directorio al terminar la transmisión.

## Contrato

- Detalle de campos y errores: `estilos/API.md`.
- `AttachmentMetadata.preview`: data URI JPEG de hasta 480 px o `null`.
- `AttachmentMetadata.preview_source`: `image` (el adjunto es imagen) o `embedded` (miniatura guardada por DWG, DXF u Office).
- `AttachmentMetadata.content_id`: Content-ID sin `<>`; el cuerpo lo referencia como `[cid:…]`.
- Índice de adjunto: posición en `attachments` de la respuesta (OLE primero, luego recuperados).

## Seguridad y recursos

- Loopback, Host y Origin locales; el resto se rechaza antes de leer el cuerpo.
- Hijo con `logging` desactivado, un hilo de cálculo y `RLIMIT_AS` en Linux.
- Pillow sólo abre PNG, JPEG, GIF, BMP, DIB, TIFF, WEBP, ICO y WMF/EMF; máximo 100 MP por imagen.
- ExifTool opcional: stdin, argumentos constantes, salida máxima 1 MiB, plazo de 15 s.
- ZIP de Office: límites de miembros, tamaño y relación de compresión.
- Temporales borrados en éxito, error y timeout; un apagado abrupto puede impedirlo (límite honesto).
