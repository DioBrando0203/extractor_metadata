# SPEC-01 Estructura de pantalla, navegación y responsive

Estado: implementada
Código: `src/components/layout/AppLayout.tsx`, `src/app/App.tsx`, `layout.css`, `responsive.css`, `src/features/help/`
Relacionadas: SPEC-02, SPEC-03, ADR-01, ADR-03, ADR-09

## Objetivo

Ocupar la ventana como el nuevo Outlook: nada se estira sin control, cada panel tiene su scroll y en móvil la lista y el lector se alternan.

## Comportamiento

- La app ocupa exactamente el alto de la ventana (`100dvh`); la página no hace scroll, sólo los paneles.
- Cabecera de 48 px en `--brand-80`: marca a la izquierda, buscador centrado (máximo 468 px) cuando hay correos, insignia "Sesión local" a la derecha.
- Barra de apps de 68 px sobre el lienzo `--bg-4`: "Correo" y "Ayuda" con icono y etiqueta; el activo usa icono relleno, fondo blanco, sombra y una barra de marca a la izquierda.
- La marca abre el selector de herramientas en la misma barra, sin perder la sesión MSG; ofrece Inspector MSG y KMZ/KML.
- Con correos: barra de comandos blanca (Abrir MSG, Limpiar bandeja) sobre bandeja (360 px) y lector, todos paneles blancos con radio 8 y separación de 8 px.
- Sin correos: no hay barra de comandos ni bandeja; la portada ocupa el lector sobre el lienzo.
- El correo se centra en el lector con ancho máximo `--reading-max`.
- Enlace "Saltar al contenido" visible al recibir foco.

## Contenido del lector (ReaderContent)

- Vista Ayuda: `HelpPage`.
- Sin items: `Dropzone`.
- Item con `message`: `MessageViewer`.
- Item con error: `ExtractionFailed`.
- Item en cola o en lectura: `MessageLoading`.
- Hay items y ninguno seleccionado: `EmptyState` "Selecciona un correo para leerlo".

## Responsive

- 861 px o más: barra de apps, bandeja y lector a la vez.
- 860 px o menos: maestro-detalle con `data-pane`; barra de apps abajo; paneles a sangre; botón "‹ Bandeja (n)" fijo arriba del lector.
- Seleccionar un correo muestra el lector; "Correo" en la barra de apps muestra la lista.
- 640 px o menos: marca e insignia sólo como icono; buscador ocupa el espacio libre.
- Puntero táctil: controles de 32 y 40 px.

## Criterios de aceptación

- CA-01: a 320 y 390 px no hay desborde horizontal. Prueba: `e2e/local-api.spec.ts` (móvil), `e2e/visual.spec.ts`.
- CA-02: en móvil se vuelve a la bandeja y se reabre el correo. Prueba: `e2e/local-api.spec.ts` (móvil).
- CA-03: Ayuda accesible desde la barra de apps. Prueba: `e2e/app.spec.ts`.
- CA-04: con un correo largo sólo el lector hace scroll. Prueba: manual a 1440 px.
- CA-05: al cambiar de correo el lector vuelve arriba. Prueba: manual.
- CA-06: a 1920 px la lectura no supera 1120 px. Prueba: captura `1920-02-correo.png` de `test:visual`.

## Pendientes

- Bandeja redimensionable.
- Tema oscuro (Fluent tiene tokens oscuros; requiere ADR).
