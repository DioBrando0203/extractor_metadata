# SPEC-B01 Análisis de un MSG

Estado: implementada
Código: `api/routes/messages.py` (`extract_message`), `services/worker.py`, `services/msg/`
Relacionadas: SPEC-B02, ADR-B01, ADR-B03, ADR-B07

## Objetivo

Convertir un MSG, sano o dañado, en un `MessageMetadata` con todo lo legible, sin modificar el original ni dejar rastros.

## Comportamiento

1. Rechazar con 415 si el nombre no termina en `.msg`.
2. Copiar por bloques a un temporal de la solicitud y procesar en un hijo aislado con plazo proporcional.
3. Rechazar con `INVALID_OR_CORRUPT_MSG` si no hay firma OLE.
4. Si la DIFAT está truncada y es verificable, leer de una copia reparada y avisar.
5. Leer propiedades OLE acotadas (`OleMetadata`).
6. Estrategia principal: parser MSG. Remitente, Para/CC/CCO, fecha (o `Date` del encabezado), cuerpo (texto, o HTML a texto, o stream OLE), encabezados, propiedades y adjuntos.
7. Estrategia de respaldo: si el parser falla y hay asunto, cuerpo o remitente en OLE, devolver correo `partial` con adjuntos OLE.
8. Con FAT reparada, añadir PNG/PDF completos encontrados fuera de los enlaces OLE.
9. Cada adjunto: metadatos por formato y miniatura si queda presupuesto de tiempo.
10. Acotar la respuesta: miniaturas hasta `max_total_preview_chars`, metadatos hasta `max_total_metadata_chars`.
11. `status = partial` si hay cualquier advertencia.

## Criterios de aceptación

- CA-01: MSG sintético válido devuelve asunto, remitente, cuerpo y temporal vacío. Prueba: `test_messages.py::test_actual_msg_extraction_and_cleanup`.
- CA-02: FAT truncada se recupera en copia sin tocar el original. Prueba: `test_messages.py::test_detects_recoverable_truncated_fat_header`, `::test_recovers_complete_raw_png_and_pdf_when_ole_links_are_missing`.
- CA-03: si el parser falla, se recupera desde OLE. Prueba: `test_messages.py::test_recover_text_and_attachments_when_primary_parser_fails`.
- CA-04: timeout termina el hijo y devuelve `EXTRACTION_TIMEOUT`. Prueba: `test_worker.py::test_timeout_terminates_worker_and_returns_diagnostic`.
- CA-05: textos en distintas codificaciones se decodifican. Prueba: `test_encoding.py::test_ansi_codepage_is_respected_in_parser_and_raw_metadata`.
- CA-06: la respuesta incluye la miniatura de un adjunto imagen. Prueba: `test_previews.py::test_extraction_response_includes_attachment_preview`.
- CA-07: el presupuesto de miniaturas no cambia estado ni advertencias. Prueba: `test_previews.py::test_preview_budget_drops_extra_thumbnails_without_partial`.
- CA-08: Host u Origin externos reciben 403 antes de leer el cuerpo. Prueba: `test_messages.py::test_foreign_origin_cannot_upload`, `::test_reject_rebound_host`.
- CA-09: un adjunto grande no se omite por un tope fijo. Prueba: `test_messages.py::test_attachment_is_not_omitted_by_a_fixed_size_limit`, `::test_large_msg_and_attachment_are_processed`.
