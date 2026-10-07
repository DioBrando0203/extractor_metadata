# Resultados de calidad

Última ejecución: 2026-10-06 23:00 -05:00 (America/Lima).
Entorno: Windows 11, Node v24.19.0, Chromium de Playwright, backend reiniciado con el código actual en 127.0.0.1:8000.

## Comandos

- `npm run format:check`: aprobado.
- `npm run build`: aprobado (TypeScript y Vite).
- `npm run lint`: aprobado, sin warnings.
- `npm test`: 13 archivos, 75 pruebas aprobadas.
- `npm run test:e2e`: 7 pruebas aprobadas (backend iniciado por Playwright con el código actual).
- `npm run test:visual`: 5 pruebas aprobadas (320, 390, 1024, 1440, 1920 px), sin desborde horizontal.
- `npm audit`: 0 vulnerabilidades tras instalar `@fluentui/react-icons` y retirar `lucide-react`.

## Verificaciones destacadas

- Correo adjunto real (E2E): MSG sintético con un correo adjunto y un enlace; "Abrir Cotización interna" muestra su remitente y texto con el foco en el asunto, "Descargar informe.pdf" baja los bytes exactos con `message_path`, "Volver" regresa; el enlace muestra "XLSX · Enlace web" sin botón de descarga.
- Capturas nuevas `04b-visor-enlace` y `04c-correo-adjunto` revisadas a 320, 1024 y 1440 px: la barra "Volver" queda visible bajo la barra fija de la bandeja en móvil y la URL se corta sin desbordar.

- Descarga real: MSG sintético, botón "Descargar plano.dwg", bytes `AC1032` y nombre correctos.
- Miniatura real: un PNG adjunto llega como data URI JPEG del backend; "Ver foto.png" abre el visor con la imagen original (320 px de ancho natural), Esc lo cierra y el foco vuelve a la tarjeta.
- Visor (unitarias): navegación entre adjuntos, miniatura incrustada de DWG, panel de detalles y descarga desde el visor.
- Seguridad: miniaturas SVG o `text/html` rechazadas en la normalización; `fetch` sólo en `lib/api.ts`; sin `innerHTML` ni almacenamiento persistente.
- Imágenes en posición, pestañas, historial plegado con remitente por mensaje y asunto deducido verificado (unitarias y capturas `02-correo`, `02b-historial`, `02c-galeria`).
- MSG real del usuario (local, no versionado): remitente, asunto, destinatarios y fecha identificados; 6 mensajes citados con su remitente; sin artefactos `mailto`.
- Búsqueda: resaltado sin tildes, fragmento en la bandeja, contador e historial desplegado; imágenes reconstruidas y no recuperadas (unitarias y MSG real).
- Revisión visual de capturas: portada, correo con miniaturas y chips, visor de imagen, visor de plano con detalles, parcial, error, cargando, búsqueda y ayuda.
- Tamaños: archivos TS de 186 líneas como máximo (`App.tsx`); CSS en 14 archivos de 249 como máximo.

## No ejecutado

- Lector de pantalla real: sólo verificación por roles en pruebas.
- Prueba en Linux en esta sesión.
