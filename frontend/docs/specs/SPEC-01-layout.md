# SPEC-01 Estructura de pantalla, navegación y responsive

Estado: implementada
Código: `src/components/layout/AppLayout.tsx`, `src/app/App.tsx`, `src/features/help/`, secciones 4 y 9 de `global.css`
Relacionadas: SPEC-02, SPEC-03, ADR-01, ADR-03

## Objetivo

Ocupar la ventana como un cliente de correo de escritorio: nada se estira sin control, cada panel tiene su propio scroll y en móvil la lista y el lector se alternan.

## Comportamiento

- La app ocupa exactamente el alto de la ventana (`100dvh`); la página nunca hace scroll, sólo la bandeja y el lector.
- Columnas en escritorio: rail 72 px, bandeja 340 px (300 px bajo 1180, 380 px desde 1600), lector flexible.
- Sin archivos en la sesión no se muestra la bandeja; el lector ocupa todo el ancho con la portada.
- El contenido del lector es una tarjeta centrada con ancho máximo `--reading-max` (960 px; 1040 px desde 1600) sobre fondo `--canvas`.
- Barra superior de 48 px: marca a la izquierda, insignia "Sesión local · sin cuenta" a la derecha.
- Rail: Bandeja y Ayuda. El activo lleva `aria-current="page"`, fondo `--brand-50` e indicador lateral.
- Enlace "Saltar al contenido" visible al recibir foco.

## Contenido del lector según estado

- Vista Ayuda: `HelpPage`.
- Sin items: `Dropzone` (portada).
- Item con `message`: `MessageViewer`.
- Item con `status=error`: `ExtractionFailed`.
- Item `queued` o `extracting`: `MessageLoading`.
- Hay items pero ninguno seleccionado: `EmptyState` "Selecciona un correo para leerlo".

## Responsive

- 861 px o más: tres columnas.
- 860 px o menos: maestro-detalle. `data-pane` en `.workspace` decide si se ve la bandeja o el lector. El rail pasa a barra inferior.
- En el lector móvil aparece "‹ Bandeja (n)" fijo arriba para volver.
- Seleccionar un item muestra el lector. Pulsar Bandeja en el rail muestra la lista.
- Al agregar archivos con un correo ya abierto, en móvil se muestra la lista; si no había selección, el lector.
- 520 px o menos: la insignia de la barra superior queda sólo como icono con texto accesible.
- Punteros táctiles: controles de 40 px (36 px los pequeños).

## Vista Ayuda

Tarjeta con pasos numerados, explicación de "lectura parcial", qué hacer si falla un archivo y aviso de privacidad.

## Criterios de aceptación

- CA-01: a 320 y 390 px no hay desborde horizontal del documento. Prueba: `e2e/local-api.spec.ts` (móvil).
- CA-02: en móvil se puede volver a la bandeja y reabrir el correo. Prueba: `e2e/local-api.spec.ts` (móvil).
- CA-03: la Ayuda es accesible desde el rail y muestra "Cómo analizar un MSG". Prueba: `e2e/app.spec.ts`.
- CA-04: con un correo largo, sólo el lector hace scroll y la bandeja queda fija. Prueba: manual a 1440 px.
- CA-05: al cambiar de correo el lector vuelve arriba. Prueba: manual.
- CA-06: a 1920 px la tarjeta de lectura no supera 1040 px de ancho. Prueba: manual con captura.

## Pendientes

- Ancho de la bandeja no redimensionable por el usuario.
- Sin tema oscuro.
