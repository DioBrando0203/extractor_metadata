# Arquitectura del frontend

Cliente React local que abre `.msg` mediante el backend en loopback y los presenta como un cliente de correo: bandeja a la izquierda, panel de lectura a la derecha. Decisiones y motivos en `decisiones/ADR.md`.

## Estructura

```text
src/
  main.tsx                         monta App e importa la hoja global
  app/App.tsx                      composición, vista activa, panel móvil y estado de selección
  app/styles/global.css            tokens y estilos de toda la app, por secciones
  components/layout/AppLayout.tsx  barra superior, rail, columnas, botón volver y overlay
  components/ui/                   Button, Avatar, EmptyState, StatusAlert (sin dominio)
  features/ingestion/              portada, bandeja, cola de extracción, arrastre y error de lectura
  features/message-viewer/         panel de lectura y esqueleto de carga
  features/attachments/            lista de adjuntos, descarga y clasificación por tipo
  features/help/                   guía rápida
  lib/api.ts                       único punto HTTP y normalización del contrato
  lib/types.ts                     tipos del contrato ya normalizado
  lib/mail.ts                      direcciones, destinatarios, título y vista previa (puro)
  lib/formatters.ts                bytes, fechas y limpieza de texto (puro)
e2e/                               Playwright contra el backend real
```

## Dependencias permitidas

- `app` puede importar todo.
- `features/*` importan `components/*` y `lib/*`.
- `features/message-viewer` compone `features/attachments/components/AttachmentList` (única dependencia entre features, documentada en ADR-05).
- `components/*` no importan `features/*`, `lib/api.ts` ni `lib/types.ts`.
- `lib/*` no importa React ni componentes.
- Ningún componente llama a `fetch`; sólo `lib/api.ts`.

## Flujo de datos

1. El usuario elige archivos (input oculto en `App`) o los suelta en cualquier parte de la ventana (`useWindowFileDrop`).
2. `useExtractionQueue.addFiles` valida la extensión, crea items `queued` o `error` y selecciona el primero si no había selección.
3. La cola procesa de uno en uno: `extracting`, luego `complete`/`partial` con `message`, o `error` con texto.
4. `lib/api.extractMessage` envía multipart a `POST /api/messages/extract` y normaliza la respuesta a `Message`.
5. `App` decide el contenido del lector según la vista y el item seleccionado (tabla de estados en SPEC-01).
6. `AttachmentList` descarga bajo demanda con `lib/api.downloadAttachment`, que reenvía el MSG en memoria y el índice del adjunto a `POST /api/messages/attachment`.

## Estado

- `useExtractionQueue`: items, selección, cola pendiente. Usa refs para no revivir items tras `clear()` durante una petición en curso.
- `App`: vista activa (`analysis` o `help`) y panel móvil (`list` o `reader`).
- `MessageViewer` se monta con `key={item.id}`: plegado de adjuntos y descargas se reinician al cambiar de correo.
- `AppLayout` devuelve el scroll del lector al inicio cuando cambia `contentKey`.
- No hay estado global, contexto ni almacenamiento persistente.

## Contrato con el backend

- `POST /api/messages/extract`: multipart `file`. Respuesta `{ message, processed_locally }`.
- `POST /api/messages/attachment`: multipart `file` y `attachment_index`. Respuesta binaria con `Content-Disposition`.
- `Message`: file_name, file_size_bytes, subject, sender, recipients (líneas `Para:`/`CC:`/`CCO:`), sent_at, received_at, body_preview, body_truncated, headers, properties, attachments, warnings, status (`complete`/`partial`).
- `headers`, `properties` y `warnings` se normalizan pero no se muestran en la vista principal.
- Base URL: `VITE_API_URL`; por defecto `http://127.0.0.1:8000/api` en desarrollo y `/api` en el build servido por FastAPI.

## Seguridad y privacidad

- Cuerpo del correo siempre como texto en `<pre>`; nunca HTML.
- Las referencias a `File` sólo viven en el estado de la cola; `clear()` las suelta.
- Las URLs `blob:` de descarga se revocan inmediatamente tras el clic.
- Sin localStorage, IndexedDB, cookies, analítica ni recursos remotos. El favicon es un SVG en línea.

## Archivos clave por tarea

- Cambiar qué se ve al abrir un correo: `features/message-viewer/components/MessageViewer.tsx` y SPEC-03.
- Cambiar la bandeja o la cola: `features/ingestion/` y SPEC-02.
- Cambiar paneles, navegación o responsive: `components/layout/AppLayout.tsx`, sección 4 y 9 de `global.css`, SPEC-01.
- Cambiar adjuntos: `features/attachments/` y SPEC-04.
