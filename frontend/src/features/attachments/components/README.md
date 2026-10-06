# Componentes de adjuntos

- `AttachmentList`: cabecera "N datos adjuntos", plegado a partir de 6, descargas y apertura del visor. SPEC-04.
- `AttachmentTiles`: `PreviewCard` (miniatura de frente) y `FileChip` (icono de tipo), ambos con botón de descarga.
- `AttachmentViewer`: diálogo a pantalla completa con navegación, detalles y descarga. SPEC-05.
- `AttachmentPreview`: contenido según `viewerMode` (imagen, conversión, PDF, texto, vídeo, audio, miniatura incrustada o sin vista).
- `AttachmentDetails`: propiedades del adjunto leídas por el backend.
- `FileTypeIcon`: icono Fluent por tipo con color de `--kind-*`.

Binarios con `hooks/useAttachmentFiles` (caché por correo, URLs revocadas al cerrar). `message-viewer` compone `AttachmentList` (ADR-05).
