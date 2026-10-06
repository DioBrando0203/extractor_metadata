# Arquitectura del frontend

Cliente React local con el aspecto del nuevo Outlook: cabecera con buscador, barra de apps, barra de comandos, bandeja y panel de lectura. Abre `.msg` mediante el backend en loopback. Decisiones en `decisiones/ADR.md`; patrones en `patrones/PATRONES.md`.

## Estructura

```text
src/
  main.tsx                               monta App e importa global.css
  app/App.tsx                            estado de vista, panel móvil, búsqueda; ReaderContent decide el lector
  app/styles/global.css                  índice de imports; un CSS por módulo (tokens, base, ui-*, layout, ...)
  components/layout/AppLayout.tsx        cabecera, barra de apps, workspace con huecos, volver móvil, overlay
  components/ui/                         Button, SearchBox, Tabs, Highlight, Avatar, StatusAlert, EmptyState, Spinner
  features/ingestion/
    components/Dropzone.tsx              portada
    components/QueueList.tsx, QueueRow.tsx  bandeja y filas
    components/ExtractionFailed.tsx      error de lectura en el lector
    components/DropOverlay.tsx           aviso al arrastrar sobre la bandeja
    hooks/useExtractionQueue.ts          cola secuencial, reintento, limpieza
    hooks/useWindowFileDrop.ts           arrastre en toda la ventana
    lib/validation.ts, lib/search.ts     extensión .msg y filtro de la bandeja
  features/message-viewer/
    components/MessageViewer.tsx         composición: título, tarjeta, pestañas, adjuntos, cuerpo y visor
    components/MessageTitle.tsx          asunto, origen del título y aviso de lectura parcial
    components/SenderBlock.tsx           remitente, fecha y destinatarios
    components/RecipientList.tsx         Para/CC/CCO con plegado
    components/MessageBody.tsx           mensaje actual e historial citado
    components/InlineContent.tsx         párrafos con imágenes incrustadas en su posición
    components/QuotedThread.tsx          mensajes anteriores plegables con su remitente
    components/MessageLoading.tsx        esqueleto
  features/attachments/
    components/AttachmentList.tsx        cabecera, plegado, descargas y apertura del visor
    components/AttachmentTiles.tsx       PreviewCard (miniatura) y FileChip (icono)
    components/AttachmentViewer.tsx      diálogo a pantalla completa, navegación y descarga
    components/AttachmentPreview.tsx     contenido según modo: imagen, PDF, texto, media, miniatura, sin vista
    components/AttachmentDetails.tsx     panel de propiedades del adjunto
    components/FileTypeIcon.tsx          icono Fluent por tipo
    hooks/useAttachmentFiles.ts          caché de binarios y URLs blob
    lib/fileKind.ts, lib/viewerMode.ts, lib/decodeText.ts
  features/help/components/HelpPage.tsx  guía rápida
  lib/api.ts                             único punto HTTP y normalización
  lib/types.ts                           contrato normalizado
  lib/mail.ts, lib/formatters.ts         utilidades puras (direcciones, título con asunto deducido, texto)
  lib/thread.ts                          hilo citado, marcadores [cid:…] y asunto deducido verificado
  lib/textSearch.ts                      búsqueda sin tildes con rangos sobre el texto original y fragmentos
e2e/                                     Playwright: funcional (backend real) y visual (@visual)
```

## Dependencias permitidas

- `app` importa todo.
- `features/*` importan `components/*` y `lib/*`.
- `features/message-viewer` compone la API pública de attachments: `AttachmentList`, `AttachmentViewer` y `useAttachmentFiles` (ADR-05). Nada más cruza features.
- `components/*` no importan `features/*`, `lib/api.ts` ni `lib/types.ts`.
- `lib/*` no importa React.
- Sólo `lib/api.ts` usa `fetch`.

## Flujo de datos

1. Archivos desde el input oculto de `App` ("Abrir MSG", portada) o soltados en la ventana (`useWindowFileDrop`).
2. `useExtractionQueue` valida, encola y procesa de uno en uno con `lib/api.extractMessage`.
3. `filterQueue` filtra la bandeja con el texto del buscador en todos los correos cargados (archivo, asunto, personas, correos electrónicos, texto con historial y nombres de adjuntos); la selección no cambia al filtrar. Cada fila resalta la coincidencia y `matchPreview` muestra dónde aparece. `MessageViewer` recibe los términos por `HighlightContext` (`features/message-viewer/highlight.ts`) y los resalta con `Highlight`.
4. `ReaderContent` elige el contenido del lector (SPEC-01).
5. `MessageViewer` muestra el correo. `splitThread` separa el mensaje actual del historial y `parseInline` coloca cada `[cid:…]` como miniatura del adjunto con ese Content-ID o nombre.
6. Si hay imágenes en posición aparecen las pestañas Mensaje (adjuntos restantes y cuerpo) y Datos adjuntos (galería completa); si no, la lista va sobre el cuerpo sin pestañas.
7. `MessageViewer` es dueño de `useAttachmentFiles` y del visor: lo abren la lista y las imágenes del cuerpo. Abrir un adjunto monta `AttachmentViewer`; `viewerMode` decide cómo mostrarlo y `useAttachmentFiles` pide el binario (`fetchAttachment`, con `preview=true` para TIFF/EMF) una sola vez.
8. Descargar reutiliza el binario en caché si existe; si no, lo pide y lo guarda con `saveBlob`.

## Estado

- `useExtractionQueue`: items, selección y cola, con refs para no revivir items tras `clear()`.
- `App`: vista, panel móvil y texto de búsqueda.
- `AttachmentList`: plegado, descargas en curso, error y adjunto abierto en el visor.
- `useAttachmentFiles`: promesas y URLs `blob:` por adjunto; se revocan al desmontar el lector.
- `MessageViewer key={id}` y `AttachmentPreview key={index}` reinician su estado al cambiar de entidad.
- Sin estado global ni almacenamiento persistente.

## Contrato con el backend

- `POST /api/messages/extract` → `{ message, processed_locally }`.
- `POST /api/messages/attachment` con `file`, `attachment_index` y `preview` opcional → binario.
- `Attachment.preview`: data URI raster validada en `lib/api.ts` (sólo jpeg, png, gif, webp en base64); `preview_source`: `image` o `embedded`.
- Detalle completo: `backend/docs/estilos/API.md`.

## Seguridad y privacidad

- Cuerpo del correo como texto en `<pre>`; adjuntos de texto en `<pre>` decodificados con `decodeText`. Nunca HTML.
- PDF en `<iframe>` con URL `blob:` y tipo `application/pdf`: lo dibuja el visor del navegador (ADR-11).
- SVG sólo en `<img>` (no ejecuta scripts). Miniaturas SVG rechazadas en la normalización.
- URLs `blob:` revocadas al desmontar o tras la descarga. Sin localStorage, IndexedDB, analítica ni recursos remotos.

## Archivos clave por tarea

- Qué se ve al abrir un correo: `MessageViewer.tsx`, SPEC-03.
- Adjuntos y visor: `features/attachments/`, SPEC-04 y SPEC-05.
- Bandeja, cola, búsqueda: `features/ingestion/`, SPEC-02.
- Paneles, cabecera, barra de comandos, responsive: `AppLayout.tsx`, `layout.css`, `responsive.css`, SPEC-01.
