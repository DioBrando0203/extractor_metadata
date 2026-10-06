# Resultados de calidad

Última ejecución: 2026-10-05 21:05 -05:00 (America/Lima).
Entorno: Windows 11, Node v24.19.0, Chromium de Playwright, backend local en 127.0.0.1:8000.

## Comandos

- `npm run format:check`: aprobado.
- `npm run build`: aprobado (TypeScript y Vite).
- `npm run lint`: aprobado, sin warnings.
- `npm test`: 6 archivos, 28 pruebas aprobadas.
- `npm run test:e2e`: 5 pruebas aprobadas.
- `npm run test:visual`: 5 pruebas aprobadas (320, 390, 1024, 1440, 1920 px), sin desborde horizontal.

## Verificaciones destacadas

- Descarga real: MSG sintético de `msg_factory.py`, clic en el adjunto, nombre `plano.dwg` y bytes `AC1032` correctos.
- Vista sin pestañas ni diagnósticos técnicos (unitarias y E2E).
- Móvil 320 y 390 px: botón de descarga visible, volver a la bandeja y reabrir el correo.
- Build servido por FastAPI en el mismo origen extrae un MSG.
- Revisión visual manual de capturas: portada, correo completo, lectura parcial, error, cargando, ayuda y overlay de arrastre.
- Búsqueda de seguridad: `fetch` sólo en `lib/api.ts`; sin `innerHTML`, `dangerouslySetInnerHTML`, localStorage ni IndexedDB.

## No ejecutado

- `npm audit`: no se cambiaron dependencias en esta tarea.
- Lector de pantalla real: sólo verificación por roles en pruebas.
