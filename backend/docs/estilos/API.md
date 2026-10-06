# Contrato y estilo de API

## Convenciones

- Rutas en minúsculas bajo `/api`, sustantivos (`/messages/extract`).
- JSON `snake_case`, fechas ISO-8601, tamaños en bytes.
- Errores: `{"detail": {"code": "CODIGO", "message": "texto seguro"}}` o `{"detail": "texto"}` en validaciones de FastAPI.
- Nunca devolver trazas, rutas temporales ni datos de otro análisis.

## Endpoints

- `GET /api/health`: `{"status": "ok", "storage": "none"}`.
- `POST /api/messages/extract`: multipart `file` (.msg). Respuesta `ExtractionResponse { message, processed_locally }`.
- `POST /api/messages/attachment`: multipart `file`, `attachment_index` (entero ≥ 0) y `preview` (booleano, opcional). Respuesta binaria con `Content-Disposition`. Con `preview=true`: `image/jpeg` de hasta 2048 px.

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

## AttachmentMetadata

- `name`, `content_type`, `size_bytes`.
- `metadata`: `MetadataItem[]` agrupados (`Archivo`, `Imagen`, `PDF`, `Office`, `AutoCAD`, `ExifTool`…).
- `warnings`.
- `preview`: `data:image/jpeg;base64,…` de hasta 480 px o `null`.
- `preview_source`: `image` o `embedded` o `null`.
- `content_id`: Content-ID sin `<>` o `null`; enlaza el adjunto con su `[cid:…]` del cuerpo.

## Códigos de error

- HTTP 415: archivo sin extensión `.msg`.
- HTTP 403: Host u Origin no locales.
- HTTP 422 con `code`:
  - `INVALID_OR_CORRUPT_MSG`: sin firma OLE o contenedor ilegible.
  - `NOT_A_MSG`: OLE válido sin propiedades de mensaje.
  - `UNREADABLE_MSG`: abre pero no hay asunto, cuerpo ni remitente recuperables.
  - `EXTRACTION_TIMEOUT`: superó el plazo proporcional al tamaño.
  - `WORKER_FAILED`, `EXTRACTION_FAILED`, `ATTACHMENT_FAILED`: el proceso aislado falló.
  - `ATTACHMENT_NOT_FOUND`, `UNREADABLE_ATTACHMENT`: índice inexistente o adjunto ilegible.
  - `NO_PREVIEW`: se pidió `preview=true` y el adjunto no tiene vista previa.
