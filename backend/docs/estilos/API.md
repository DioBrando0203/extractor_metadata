# Contrato y estilo de API

## Convenciones

- Rutas en minúsculas bajo `/api`, sustantivos (`/messages/extract`).
- JSON `snake_case`, fechas ISO-8601, tamaños en bytes.
- Errores: `{"detail": {"code": "CODIGO", "message": "texto seguro"}}` o `{"detail": "texto"}` en validaciones de FastAPI.
- Nunca devolver trazas, rutas temporales ni datos de otro análisis.

## Endpoints

- `GET /api/health`: `{"status": "ok", "storage": "none"}`.
- `POST /api/messages/extract`: multipart `file` (.msg). Respuesta `ExtractionResponse { message, processed_locally }`.
- `POST /api/messages/attachment`: multipart `file`, `attachment_index` (entero ≥ 0), `preview` (booleano, opcional) y `message_path` (opcional, posiciones de correos adjuntos separadas por `/`, p. ej. `2/0`, hasta `max_embedded_depth` niveles). Respuesta binaria con `Content-Disposition`. Con `preview=true`: `image/jpeg` de hasta 2048 px. Un adjunto `kind=message` se entrega como `.msg` con `application/vnd.ms-outlook` o, si es un EML, como `.eml` con `message/rfc822`.

## MessageMetadata

- `file_name`, `file_size_bytes`.
- `subject`, `sender`: texto o `null`.
- `recipients`: líneas `Para: …`, `CC: …`, `CCO: …` con direcciones separadas por `;`, del parser o, si faltan, de propiedades MAPI o encabezados de transporte.
- `sent_at`, `received_at`: ISO-8601 o `null`.
- `body_preview`: texto plano (HTML convertido a texto) o `null`; las imágenes incrustadas aparecen como `[cid:<content-id>]` en su posición; `body_truncated`.
- `status`: `complete` o `partial` (hay advertencias).
- `headers`, `properties`: `MetadataItem[]` diagnósticos; el frontend no los muestra.
- `attachments`: `AttachmentMetadata[]`; su posición es el índice para `/attachment`.
- `warnings`: textos para diagnóstico.
- `item`: `null` en un correo; en otra clase de mensaje, `ItemDetails`:
  - `kind`: `meeting` (IPM.Schedule.Meeting.Request), `cancellation` (…Canceled), `response` (…Resp.*), `appointment` (IPM.Appointment), `contact` (IPM.Contact), `task` (IPM.Task y IPM.TaskRequest).
  - `start`, `end`: ISO-8601 o `null`; en una tarea, inicio y vencimiento.
  - `all_day`, `location`.
  - `fields`: `MetadataItem[]` en orden de lectura (organizador, obligatorios, opcionales, repetición, respuesta; o nombre, correo, empresa, teléfonos; o estado, avance, responsable).

## AttachmentMetadata

- `name`, `content_type`, `size_bytes`.
- `metadata`: `MetadataItem[]` agrupados (`Archivo`, `Imagen`, `PDF`, `Office`, `AutoCAD`, `ExifTool`…).
- `warnings`.
- `preview`: `data:image/jpeg;base64,…` de hasta 480 px o `null`.
- `preview_source`: `image` o `embedded` o `null`.
- `content_id`: Content-ID sin `<>` o `null`; enlaza el adjunto con su `[cid:…]` del cuerpo.
- `content_id_inferred`: `true` si el Content-ID se reconstruyó por las medidas de la imagen (archivo dañado); la interfaz lo indica.
- `kind`: `file` (por defecto), `message` o `link`.
- `message`: `MessageMetadata` del correo adjunto (carpeta OLE, `.msg` o `.eml` adjunto) o `null` (fuera del presupuesto o ilegible; entonces `warnings` dice por qué). Sólo con `kind=message`.
- `link`: URL o ruta de red de un adjunto por referencia, como texto; el backend nunca la abre. `null` si no se pudo leer. Sólo con `kind=link`.

## Códigos de error

- HTTP 415: archivo sin extensión `.msg`.
- HTTP 422 de validación: `message_path` con otro formato o más de `max_embedded_depth` niveles.
- HTTP 403: Origin fuera de `APP_ALLOWED_ORIGINS` (loopback por defecto). Un Host fuera de `APP_ALLOWED_HOSTS` recibe 400 de `TrustedHostMiddleware`.
- HTTP 422 con `code`:
  - `INVALID_OR_CORRUPT_MSG`: sin firma OLE o contenedor ilegible.
  - `NOT_A_MSG`: OLE válido sin propiedades de mensaje.
  - `UNREADABLE_MSG`: abre pero no hay asunto, cuerpo ni remitente recuperables.
  - `EXTRACTION_TIMEOUT`: superó el plazo proporcional al tamaño.
  - `WORKER_FAILED`, `EXTRACTION_FAILED`, `ATTACHMENT_FAILED`: el proceso aislado falló.
  - `ATTACHMENT_NOT_FOUND`, `UNREADABLE_ATTACHMENT`: índice inexistente, `message_path` que no lleva a un correo adjunto, adjunto ilegible o enlace sin bytes.
  - `NO_PREVIEW`: se pidió `preview=true` y el adjunto no tiene vista previa.
