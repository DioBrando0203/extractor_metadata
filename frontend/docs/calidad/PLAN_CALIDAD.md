# Plan de calidad

Reglas en `reglas_calidad/REGLAS.md`. Última ejecución en `RESULTADOS.md`.

## Capas de prueba

- Unitarias (Vitest): lógica pura.
  - `src/lib/mail.test.ts`: direcciones, separación de destinatarios, agrupación Para/CC/CCO, título y vista previa.
  - `src/lib/formatters.test.ts`: bytes, fechas de encabezado y bandeja, limpieza de texto.
  - `src/lib/api.test.ts`: normalización del contrato y error de red.
  - `src/features/attachments/lib/fileKind.test.ts`: clasificación por extensión y MIME.
  - `src/features/attachments/lib/viewerMode.test.ts`: modos del visor y decodificación de texto.
  - `src/features/ingestion/lib/search.test.ts`: búsqueda sin tildes ni mayúsculas, también en adjuntos.
  - `src/features/ingestion/hooks/useExtractionQueue.test.tsx`: cola secuencial, reintento y limpieza durante una petición.
- Componente (React Testing Library): `MessageViewer.test.tsx` cubre SPEC-03 y el plegado de SPEC-04; `AttachmentList.test.tsx` cubre miniaturas, chips, visor (abrir, navegar, cerrar con foco devuelto), detalles y descarga.
- E2E funcional (Playwright, backend real): `e2e/app.spec.ts` y `e2e/local-api.spec.ts`. Portada, Ayuda, extracción, descarga de bytes reales, miniatura real y visor con imagen del backend, móvil 320/390 sin desborde, maestro-detalle y build servido por FastAPI.
- E2E visual (Playwright, respuestas simuladas): `e2e/visual.spec.ts` con datos de `e2e/visual-fixtures.ts` (PNG sintéticos generados en la prueba), etiqueta `@visual`. Captura portada, correo, visor de imagen, visor de plano con detalles, bandeja móvil, parcial, error, cargando, búsqueda y ayuda en 320, 390, 1024, 1440 y 1920 px; falla si hay desborde horizontal.

## Comandos

Desde `frontend/`:

- `npm run format:check`
- `npm run build`
- `npm run lint`
- `npm test`
- `npm run test:e2e`: funcional, excluye `@visual`. Ejecutar `npm run build` antes (el lanzador sirve `dist`).
- `npm run test:visual`: genera `test-results/capturas/<ancho>-<estado>.png`. Revisar las imágenes; la prueba sólo garantiza ausencia de desborde.

Playwright arranca o reutiliza el backend en `http://127.0.0.1:8000` (`/api/health`) con `py ../iniciar.py --sin-navegador` en Windows o `python3` en Linux, y Vite en el puerto 5173.

## Revisión visual manual

Tras `npm run test:visual`, revisar en las capturas:

- Jerarquía: asunto, remitente, adjuntos y cuerpo se distinguen sin esfuerzo.
- Alineación: avatar, nombre y fecha en la misma línea base; tarjetas de adjuntos de igual alto.
- Recortes: nombres largos con elipsis; asuntos largos en varias líneas sin cortar palabras de forma rara.
- Densidad: ninguna zona vacía desproporcionada; nada estirado a todo el ancho en 1920 px.
- Estados: parcial, error y cargando son reconocibles sin leer todo el texto.

## Accesibilidad

- Teclado: Tab recorre rail, Abrir MSG, Limpiar, filas, adjuntos y enlaces en orden.
- Lectores de pantalla: bandeja `aside` con nombre, lector `main`, correo `article` etiquetado por el asunto, carga con `role="status"`, errores con `role="alert"`.
- Contraste: tokens de texto verificados AA; no usar `--subtle` para texto.
- Movimiento: spinner y esqueleto se detienen con `prefers-reduced-motion: reduce`.

## Privacidad y seguridad

- Buscar en el código `dangerouslySetInnerHTML`, `innerHTML`, `localStorage`, `indexedDB`, `fetch(`. Sólo se permite `fetch` en `lib/api.ts`.
- Confirmar que no hay recursos remotos en `index.html` ni en CSS.
- Archivos de más de 10 MB: el backend los acepta; el corpus grande se prueba en backend.
