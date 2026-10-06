# SPEC-04 Adjuntos

Estado: implementada
Código: `src/features/attachments/`, `src/lib/api.ts` (`downloadAttachment`)
Relacionadas: SPEC-03, ADR-04

## Objetivo

Ver de un vistazo qué archivos trae el correo y descargar cualquiera con un clic.

## Comportamiento

- Cabecera: clip, "N adjunto(s)" y tamaño total entre paréntesis si se conoce algún tamaño.
- Rejilla de tarjetas: columnas automáticas con mínimo 260 px; una sola columna en móvil.
- Tarjeta: icono por tipo sobre fondo tenue, nombre (una línea con elipsis y `title` completo), tipo y tamaño, icono de descarga.
- Toda la tarjeta es el botón. Nombre accesible: "Descargar <nombre>".
- Más de 6 adjuntos: se muestran 6 y un botón "Mostrar los N" / "Mostrar menos" con `aria-expanded`.
- Descarga: la tarjeta queda deshabilitada con spinner y "Preparando descarga…" hasta terminar. Se pueden descargar varias a la vez.
- Error de descarga: mensaje `role="alert"` bajo la rejilla: "No se pudo descargar “nombre”. Inténtalo otra vez."
- El índice enviado al backend es la posición en la lista completa, no en la visible.

## Clasificación por tipo (`fileKind`)

- Por extensión primero; si no hay, por MIME.
- Grupos: pdf, word, excel, slides, image, cad, archive, mail, text, media, other.
- Etiqueta: extensión en mayúsculas o, sin extensión, descripción genérica ("Imagen", "Archivo").
- Colores en tokens `--kind-*`; el color nunca es la única señal (hay icono y etiqueta).

## Estados

- Carga: tarjeta en descarga con spinner.
- Vacío: la sección no se renderiza.
- Éxito: el navegador inicia la descarga con el nombre de `Content-Disposition`.
- Parcial: adjuntos sin tamaño muestran "—".
- Error: mensaje de alerta; la tarjeta vuelve a estar disponible.

## Criterios de aceptación

- CA-01: pulsar un adjunto descarga los bytes correctos con su nombre. Prueba: `e2e/local-api.spec.ts`.
- CA-02: con 9 adjuntos se ven 6 y se pueden expandir a 9. Prueba: `MessageViewer.test.tsx`.
- CA-03: la clasificación prioriza la extensión y cae al MIME. Prueba: `fileKind.test.ts`.
- CA-04: a 320 px el botón de descarga es visible sin desborde. Prueba: `e2e/local-api.spec.ts`.

## Pendientes

- Vista previa de imágenes y PDF.
- Descargar todos en un ZIP.
- Ocultar imágenes en línea de firmas.
