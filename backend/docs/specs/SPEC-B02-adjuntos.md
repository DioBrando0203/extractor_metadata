# SPEC-B02 Adjuntos: descarga, miniaturas y vista previa

Estado: implementada
Código: `services/msg/download.py`, `services/msg/attachments.py`, `services/previews/`, `services/metadata/`
Relacionadas: SPEC-B01, frontend SPEC-04 y SPEC-05, ADR-B02, ADR-B05, ADR-B06

## Objetivo

Que cualquier adjunto se pueda descargar con sus bytes exactos y que imágenes, planos y documentos con portada se puedan ver sin descargarlos.

## Descarga

- `POST /attachment` con `attachment_index` copia el stream del adjunto a un temporal y lo envía con nombre seguro y MIME por extensión o firma.
- Índices: adjuntos OLE en orden de carpeta y, después, recuperados de datos sueltos.
- `message_path` (`"2/0"`): abre cada correo adjunto en orden y aplica el índice dentro del último. Cada nivel se copia a un MSG propio dentro del temporal de la descarga.
- Correo adjunto: se entrega como `.msg` legible por Outlook y por esta aplicación.
- Enlace (`kind=link`): no tiene bytes; responde `UNREADABLE_ATTACHMENT`.
- El directorio temporal se borra al terminar la transmisión o ante cualquier error.

## Miniatura en el análisis

- Fuente `image`: el adjunto es una imagen de la lista cerrada.
- Fuente `embedded`: DWG (sección de imagen en la dirección 0x0D, PNG código 6 o BMP código 2), DXF (sección `THUMBNAILIMAGE`, DIB en hexadecimal) u Office (`docProps/thumbnail.jpeg|jpg|png`).
- Salida: JPEG de hasta 480 px, calidad 82, transparencia sobre blanco, orientación EXIF aplicada.
- Se omite sin error si: el formato no está permitido, supera 64 MB o 100 MP, está dañado, se agotó el presupuesto de tiempo o el de tamaño.

## Vista previa grande

- `POST /attachment` con `preview=true`: el mismo proceso extrae el adjunto y lo sustituye por un JPEG de hasta 2048 px.
- Sin vista previa posible: 422 `NO_PREVIEW`.
- Uso: TIFF, EMF y otras imágenes que el navegador no muestra.

## Criterios de aceptación

- CA-01: un PDF adjunto se descarga con bytes, nombre y MIME correctos. Prueba: `test_messages.py::test_attachment_can_be_downloaded_and_is_cleaned_up`.
- CA-02: miniaturas de PNG, JPEG, GIF, BMP, TIFF y WEBP. Prueba: `test_previews.py::test_common_image_formats_have_preview`.
- CA-03: miniatura DWG en PNG y en BMP; sección rota o ausente se ignora. Prueba: `test_previews.py::test_dwg_png_preview_saved_by_autocad`, `::test_dwg_bmp_preview_saved_by_autocad`, `::test_dwg_without_preview_or_with_broken_section_is_ignored`.
- CA-04: miniatura DXF y Office. Prueba: `test_previews.py::test_dxf_thumbnailimage_section`, `::test_office_docprops_thumbnail`.
- CA-05: EPS y PDF no se decodifican como imagen. Prueba: `test_previews.py::test_unsupported_or_dangerous_formats_are_not_decoded`.
- CA-06: `preview=true` convierte TIFF a JPEG y responde `NO_PREVIEW` sin vista previa, dejando el temporal vacío. Prueba: `test_previews.py::test_large_preview_endpoint_converts_tiff_to_jpeg`, `::test_large_preview_endpoint_rejects_files_without_preview`.
- CA-07: metadatos DWG informan "Miniatura incrustada". Prueba: `test_previews.py::test_dwg_metadata_reports_embedded_thumbnail`.
- CA-08: un adjunto dentro de un correo adjunto se descarga con `message_path`. Prueba: `test_embedded.py::test_inner_attachment_downloads_through_the_message_path`.
- CA-09: un correo adjunto se descarga como `.msg` que vuelve a leerse completo. Prueba: `test_embedded.py::test_attached_message_downloads_as_a_readable_msg`.
- CA-10: `message_path` mal formado, demasiado profundo o que no lleva a un correo adjunto se rechaza. Prueba: `test_embedded.py::test_invalid_message_path_is_rejected`, `::test_message_path_must_point_to_an_attached_message`.
- CA-11: un enlace no ofrece descarga vacía. Prueba: `test_embedded.py::test_cloud_attachment_is_a_link_without_bytes`.
- CA-12: `message_path` entra en un `.eml` adjunto, en el correo que contiene y en un `.msg` adjunto; un índice que no es un correo responde 422. Prueba: `test_eml.py::test_attachments_inside_an_eml_download_through_the_message_path`, `::test_msg_attached_as_a_file_is_read_and_its_attachments_download`.
