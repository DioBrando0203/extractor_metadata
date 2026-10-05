# Arquitectura de frontend

## Objetivo

Una UI local, responsive y accesible para elegir/arrastrar un MSG y explicar claramente lo recuperado, lo parcial y lo ilegible. No guarda archivos ni requiere cuenta.

## Árbol y responsabilidad

```text
src/
  app/                 composición global y estilos globales
  components/ui/       componentes realmente reutilizables y sin dominio
  components/layout/   estructura compartida
  features/
    ingestion/         dropzone y validación de carga
    message-viewer/    lectura y pestañas del MSG
    attachments/       lista desplegable y metadata de adjuntos
  lib/                 contrato API, formateadores y tipos
```

Una página o `App` compone features: no incluye reglas de negocio de extracción. Los componentes específicos permanecen dentro de su feature; sólo se suben a `components/ui` cuando dos dominios los usan sin conocimiento del MSG.

## Flujo y contrato

`Dropzone` acepta múltiples archivos y `useExtractionQueue` los ejecuta secuencialmente: un fallo individual no detiene la cola. `lib/api.ts` envía cada archivo como `multipart/form-data` a `POST /api/messages/extract`, normaliza tanto el contrato anterior como los nuevos campos (`status`, `body_truncated`, `headers`) y conserva todo sólo en memoria. `QueueList` permite seleccionar resultados, reintentar errores y limpiar la sesión; limpiar elimina las referencias a los archivos incluso si una petición previa termina después.

`MessageViewer` presenta asunto, remitente, cuerpo textual, avisos, encabezados, propiedades y adjuntos. Sus pestañas usan `tablist`/`tabpanel`, roving tabindex y flechas/Home/End. La exportación crea y descarga un JSON local con el resultado normalizado. `Help` explica el flujo y los diagnósticos sin remitir a contenido externo.

El cuerpo se muestra como texto (`pre`), nunca con `dangerouslySetInnerHTML`. La API no entrega binarios ni rutas reales.

## Diseño responsive y accesibilidad

En escritorio hay rail, lista y lector. Bajo 780px, la bandeja pasa a una lista horizontal superior para conservar selección y reintentos; la navegación se compacta. Toda acción es botón, los estados se anuncian con `aria-live` y el foco es visible. Mantener contraste AA.

## Comandos

`npm run dev`, `npm run build`, `npm run lint`, `npm test`, `npm run test:e2e`, `npm run format:check`.

## Mapa de archivos de continuidad

- `main.tsx`: monta App en StrictMode e importa el único stylesheet global.
- `app/App.tsx`: compone análisis/ayuda, selector múltiple, lector y estados pendiente/error.
- `components/layout/AppLayout.tsx`: layout compartido de las dos vistas.
- `components/ui/Button.tsx`, `MetadataTable.tsx`, `StatusAlert.tsx`: controles sin lógica de extracción.
- `features/ingestion/components/Dropzone.tsx`: selección/drag; `QueueList.tsx`: bandeja, reintento/limpieza.
- `features/ingestion/hooks/useExtractionQueue.ts`: única cola secuencial; refs sincrónicas y estado React.
- `features/ingestion/lib/validation.ts`: extensión y límite 100 MB antes de enviar; errores no reintentables.
- `features/message-viewer/components/MessageViewer.tsx`: resumen humano, cuerpo, headers, raw metadata y exportación.
- `features/attachments/components/AttachmentList.tsx`: detalles y avisos por adjunto.
- `lib/api.ts`: FormData, errores y normalización del contrato; `types.ts`: tipos compartidos.
- `lib/formatters.ts`: tamaños legibles B/KB/MB y fechas tolerantes a datos inválidos.
- `vite-env.d.ts`, `vite.config.ts`, `tsconfig.json`: tipos de entorno, build y pruebas.
- `src/test/setup.ts`, `*.test.ts(x)`: Vitest/RTL. `e2e/`: Playwright con API real y MSG sintético.

En desarrollo la API por defecto es `http://127.0.0.1:8000/api`; en build es `/api` en el mismo origen.
La opción `VITE_API_URL` se reserva para otro backend local. Las versiones exactas y sus dependencias
se fijan en package.json/package-lock.json. Node LTS mediante nvm, instalado en esta sesión.
El arranque unificado se hace con `python3 iniciar.py` desde la raíz (Windows: `py iniciar.py`).

El resumen evita mostrar todos los streams binarios; Metadatos conserva la lista técnica completa
dentro de los límites publicados del backend. Limpiar libera resultados/referencias de la sesión,
pero una solicitud ya enviada puede terminar su limpieza en el backend antes de 90 segundos.
No usar localStorage, IndexedDB ni analítica. El cuerpo nunca se inyecta como HTML.
