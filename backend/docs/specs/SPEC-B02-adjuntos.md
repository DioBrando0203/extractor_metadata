# SPEC-B02 Adjuntos: descarga, miniaturas y vista previa

Estado: implementada
Código: `services/msg/download.py`, `services/msg/attachments.py`, `services/previews/`, `services/metadata/`
Relacionadas: SPEC-B01, frontend SPEC-04 y SPEC-05, ADR-B02, ADR-B05, ADR-B06

## Objetivo

Que cualquier adjunto se pueda descargar con sus bytes exactos y que imágenes, planos y documentos con portada se puedan ver sin descargarlos.

## Descarga

- `POST /attachment` con `attachment_index` copia el stream del adjunto a un temporal y lo envía con nombre seguro y MIME por extensión o firma.
- Índices: adjuntos OLE en orden de carpeta y, después, recuperados de datos sueltos.
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
