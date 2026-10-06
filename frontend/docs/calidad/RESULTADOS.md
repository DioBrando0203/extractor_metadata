# Resultados de calidad

Última ejecución: 2026-10-06 01:11 -05:00 (America/Lima).
Entorno: Windows 11, Node v24.19.0, Chromium de Playwright, backend reiniciado con el código actual en 127.0.0.1:8000.

## Comandos

- `npm run format:check`: aprobado.
- `npm run build`: aprobado (TypeScript y Vite).
- `npm run lint`: aprobado, sin warnings.
- `npm test`: 10 archivos, 50 pruebas aprobadas.
- `npm run test:e2e`: 6 pruebas aprobadas.
- `npm run test:visual`: 5 pruebas aprobadas (320, 390, 1024, 1440, 1920 px), sin desborde horizontal.
- `npm audit`: 0 vulnerabilidades tras instalar `@fluentui/react-icons` y retirar `lucide-react`.

## Verificaciones destacadas

- Descarga real: MSG sintético, botón "Descargar plano.dwg", bytes `AC1032` y nombre correctos.
- Miniatura real: un PNG adjunto llega como data URI JPEG del backend; "Ver foto.png" abre el visor con la imagen original (320 px de ancho natural), Esc lo cierra y el foco vuelve a la tarjeta.
- Visor (unitarias): navegación entre adjuntos, miniatura incrustada de DWG, panel de detalles y descarga desde el visor.
- Seguridad: miniaturas SVG o `text/html` rechazadas en la normalización; `fetch` sólo en `lib/api.ts`; sin `innerHTML` ni almacenamiento persistente.
- Imágenes en posición, pestañas, historial plegado con remitente por mensaje y asunto deducido verificado (unitarias y capturas `02-correo`, `02b-historial`, `02c-galeria`).
- MSG real del usuario (local, no versionado): remitente, asunto, destinatarios y fecha identificados; 6 mensajes citados con su remitente; sin artefactos `mailto`.
- Revisión visual de capturas: portada, correo con miniaturas y chips, visor de imagen, visor de plano con detalles, parcial, error, cargando, búsqueda y ayuda.
- Tamaños: archivos TS de 173 líneas como máximo; CSS en 13 archivos de 248 como máximo.

## No ejecutado

- Lector de pantalla real: sólo verificación por roles en pruebas.
- Prueba en Linux en esta sesión.
