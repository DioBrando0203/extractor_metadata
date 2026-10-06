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
9. Completar asunto, remitente, destinatarios y fecha vacíos con propiedades MAPI alternativas (`0E1D`, `003D`, `0070`, `0042`, `5D01`, `5D02`, `0065`) y después con los encabezados de transporte.
10. Cuerpo con marcadores `[cid:…]` en la posición de cada imagen incrustada.
11. Cada adjunto: metadatos por formato, Content-ID y miniatura si queda presupuesto de tiempo.
12. Acotar la respuesta: miniaturas hasta `max_total_preview_chars`, metadatos hasta `max_total_metadata_chars`.
13. `status = partial` si hay cualquier advertencia.

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
- CA-10: con el parser caído y sin propiedades cortas, remitente, asunto, Para y fecha salen de los encabezados de transporte. Prueba: `test_envelope.py::test_recovered_message_identifies_sender_from_transport_headers`.
- CA-11: un asunto ausente en un MSG legible se completa desde los encabezados. Prueba: `test_envelope.py::test_parsed_message_completes_missing_subject_from_headers`.
- CA-12: se prefiere el SMTP sobre direcciones internas de Exchange y se arma el asunto con su prefijo. Prueba: `test_envelope.py::test_properties_prefer_smtp_and_skip_exchange_addresses`.
- CA-13: las imágenes HTML `cid:` quedan como marcadores en su posición y las remotas se descartan. Prueba: `test_envelope.py::test_html_images_become_position_markers_and_remote_images_are_dropped`, `::test_inline_image_keeps_content_id_and_position_in_body`.

- CA-14: el RTF comprimido suelto se recupera sólo si su CRC es válido y su texto coincide con el cuerpo legible. Prueba: `test_inline_recovery.py::test_loose_rtf_is_recovered_only_if_it_matches_the_readable_body`, `::test_corrupted_rtf_is_ignored`.
- CA-15: posición reconstruida por tamaño exacto o proporción única; lo ambiguo no se asigna y un Content-ID leído nunca se reemplaza. Prueba: `test_inline_recovery.py` (`exact_size`, `unique_aspect`, `ambiguous`, `existing_content_ids`).
- CA-16: un MSG dañado recupera el cuerpo con imágenes en posición. Prueba: `test_inline_recovery.py::test_damaged_message_gets_images_back_in_position`.
