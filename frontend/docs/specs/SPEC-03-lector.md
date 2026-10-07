# SPEC-03 Panel de lectura del correo

Estado: implementada
Código: `src/features/message-viewer/` (`MessageReader`, `MessageViewer`, `RecipientList`, `MessageLoading`), `src/lib/mail.ts`, `src/lib/formatters.ts`
Relacionadas: SPEC-04, ADR-02, ADR-07, ADR-18

## Objetivo

Al abrir un MSG el usuario ve el correo como en su cliente de correo habitual: asunto, quién lo envió, a quién, cuándo, los adjuntos y el texto, todo en una sola vista sin pestañas.

## Anatomía (de arriba abajo)

1. Barra de asunto: `h1` 20/28 semibold, fuera de la tarjeta, como en Outlook.
2. Nota de origen si el título no es el asunto real: "Asunto deducido del mensaje citado; coincide con el nombre del archivo." o "Asunto no recuperado: se muestra el nombre del archivo."
3. MessageBar de advertencia si `status=partial`.
4. Tarjeta del mensaje (blanca, radio 8, `--shadow-4`):
   1. Remitente: avatar de 40 px, nombre semibold, `<correo>` en `--fg-3`, fecha a la derecha.
   2. Destinatarios Para, CC y CCO; más de 8 se pliegan con "+N más".
   3. Pestañas Mensaje y Datos adjuntos (N), sólo si alguna imagen está en su posición (ADR-13).
   4. Datos adjuntos no incrustados (SPEC-04).
   5. Cuerpo: párrafos de texto plano con espaciado compacto e imágenes incrustadas en su posición (botón "Ver <nombre>" que abre el visor); "Imagen incrustada no disponible" si el `cid` no tiene adjunto.
   6. Historial: "Mostrar los N mensajes anteriores"; cada mensaje con avatar, remitente, correo, fecha, Para/CC (nombres; la lista completa al pasar el ratón), Asunto y su texto. Abierto por defecto si el correo no tiene texto propio.
   7. Nota si el cuerpo fue truncado.
   8. Pie: nombre del archivo `.msg` y tamaño.

## Correo adjunto (ADR-18)

- Un adjunto `kind: 'message'` con `message` se abre con "Abrir <nombre>" desde la lista o con "Abrir correo" desde el visor, y se muestra en el mismo lector con esta misma anatomía.
- Encima del asunto, la barra "Correo adjunto": botón "Volver" (nombre accesible "Volver a <asunto del contenedor>") y "Correo adjunto en <asunto>" en una línea, con el asunto completo en `title`.
- Al abrir o volver, la vista regresa al inicio y el foco pasa al asunto del correo mostrado.
- Los adjuntos del correo adjunto se ven y se descargan con su ruta (`messagePath`); la búsqueda resalta también dentro de él.
- Elegir otro correo de la bandeja vuelve al correo principal.

## Reglas de datos

- Título: asunto real; si falta, asunto deducido y verificado (ADR-15); si no, nombre del archivo sin `.msg`.
- Remitente: se separa nombre y correo de `Nombre <correo>`. Si falta: "Remitente desconocido" en cursiva y avatar genérico.
- Fecha: `sent_at` o, si falta, `received_at`. Si no hay ninguna, no se muestra nada.
- Destinatarios: si no hay, no se muestra la lista. Nunca "Sin destinatarios".
- Separación de direcciones: `;` siempre separa; `,` sólo si el tramo ya tiene `@` o `>` (no parte "Pérez, Ana").
- Cuerpo: `tidyText` unifica saltos de línea, quita espacios finales, reduce 3 o más saltos a 2 y elimina los `<mailto:…>` duplicados. No altera palabras.
- Hilo: `splitThread` (ADR-14). Imágenes: `parseInline` y `findInlineAttachment`.
- Sin cuerpo: "No se pudo recuperar el texto de este correo."
- No se muestran `headers`, `properties` ni `warnings`.

## Estados

- Carga: `MessageLoading` con `role="status"`, título "Leyendo el correo" o "En espera" y esqueleto con la misma anatomía.
- Vacío: no aplica; sin correo se muestra otro contenido (SPEC-01).
- Éxito: anatomía completa.
- Parcial: barra de lectura parcial y campos ausentes omitidos o marcados como desconocidos.
- Error: lo gestiona SPEC-02 (`ExtractionFailed`).

## Criterios de aceptación

- CA-01: asunto, remitente, adjuntos y cuerpo aparecen en la misma vista sin pestañas. Prueba: `MessageViewer.test.tsx`.
- CA-02: destinatarios agrupados como Para y CC con correo en `title`; más de 8 se pliegan y se pueden expandir. Prueba: `MessageViewer.test.tsx`.
- CA-03: bloques de líneas vacías se reducen sin alterar el texto. Prueba: `MessageViewer.test.tsx`, `formatters.test.ts`.
- CA-04: sin asunto se usa el nombre del archivo y se avisa. Prueba: `MessageViewer.test.tsx`.
- CA-05: en lectura parcial no se inventan remitente, destinatarios ni fecha. Prueba: `MessageViewer.test.tsx`.
- CA-06: no aparecen diagnósticos técnicos. Prueba: `MessageViewer.test.tsx`, `e2e/local-api.spec.ts`.
- CA-07: el HTML del correo nunca se interpreta. Prueba: revisión de código (no existe `dangerouslySetInnerHTML`).

## Accesibilidad

- `article` etiquetado por el asunto. Cuerpo en `section` con nombre "Contenido del correo".
- Avatar decorativo (`aria-hidden`); el nombre siempre está en texto.
- Fecha en `<time dateTime>`.

## Responsive

- 640 px o menos: el correo del remitente pasa a su propia línea.
- 860 px o menos: tarjeta a sangre completa, sin radio ni sombra.

## Pendientes

- Render seguro de HTML (requiere sanitizador evaluado; hoy prohibido por P-05).
- Imágenes en línea del cuerpo (`cid:`); hoy aparecen como adjuntos.
- Exportar o imprimir el correo.

## Criterios añadidos (2026-10-06)

- CA-08: imágenes incrustadas en posición y pestaña con todos los adjuntos. Prueba: `MessageViewer.test.tsx`.
- CA-09: historial plegado que identifica al remitente de cada mensaje. Prueba: `MessageViewer.test.tsx`, `lib/thread.test.ts`.
- CA-10: asunto deducido sólo si reproduce el nombre del archivo. Prueba: `MessageViewer.test.tsx`, `lib/thread.test.ts`, `lib/mail.test.ts`.
- CA-11: los `<mailto:…>` duplicados no aparecen en el texto ni en los remitentes citados. Prueba: `lib/formatters.test.ts`.

- CA-12: con búsqueda activa se resaltan asunto, remitente, destinatarios, texto e historial, se cuentan las coincidencias y el historial se despliega si la coincidencia está ahí. Prueba: `MessageViewer.test.tsx`.
- CA-13: una imagen ubicada por medidas muestra "Ubicación reconstruida" y una no recuperada se indica con "Imagen no recuperada · nombre". Prueba: `MessageViewer.test.tsx`.
- CA-14: un correo adjunto se abre en el lector con su remitente y su texto, y "Volver" regresa al contenedor; el foco va al asunto en ambos casos. Prueba: `MessageReader.test.tsx`, `e2e/local-api.spec.ts`, capturas `04c-correo-adjunto`.
- CA-15: un adjunto del correo adjunto se descarga con su ruta y sus bytes reales. Prueba: `MessageReader.test.tsx`, `e2e/local-api.spec.ts`.
- CA-16: la ruta de correos adjuntos se corta donde no hay un correo leído. Prueba: `lib/mail.test.ts` (`messageTrail`).
