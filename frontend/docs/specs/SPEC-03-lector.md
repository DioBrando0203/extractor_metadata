# SPEC-03 Panel de lectura del correo

Estado: implementada
Código: `src/features/message-viewer/`, `src/lib/mail.ts`, `src/lib/formatters.ts`
Relacionadas: SPEC-04, ADR-02, ADR-07

## Objetivo

Al abrir un MSG el usuario ve el correo como en su cliente de correo habitual: asunto, quién lo envió, a quién, cuándo, los adjuntos y el texto, todo en una sola vista sin pestañas.

## Anatomía (de arriba abajo)

1. Asunto: `h1`, 20 px semibold, ajusta en varias líneas.
2. Nota bajo el asunto si se usó el nombre del archivo: "Asunto no recuperado: se muestra el nombre del archivo."
3. Barra de lectura parcial si `status=partial`: "Lectura parcial. Es posible que falten algunos datos de este correo; se muestra todo lo que se pudo leer."
4. Remitente: avatar de 40 px, nombre en semibold, `<correo>` en gris, fecha a la derecha (`lun 05/10/2026, 20:13`).
5. Destinatarios en lista de definición: filas Para, CC y CCO. Nombre visible y correo en `title`. Más de 8 se pliegan con el botón "+N más" (nombre accesible "+N más, mostrar todos los destinatarios").
6. Adjuntos (SPEC-04) si hay al menos uno.
7. Cuerpo: texto plano, fuente de lectura, 15 px, interlineado 1.55, `pre-wrap`.
8. Nota si el cuerpo fue truncado: "El mensaje es muy largo: se muestra sólo la primera parte."
9. Pie: nombre del archivo `.msg` y su tamaño.

## Reglas de datos

- Título: asunto limpio o, si falta, nombre del archivo sin `.msg` (Outlook nombra así los MSG guardados).
- Remitente: se separa nombre y correo de `Nombre <correo>`. Si falta: "Remitente desconocido" en cursiva y avatar genérico.
- Fecha: `sent_at` o, si falta, `received_at`. Si no hay ninguna, no se muestra nada.
- Destinatarios: si no hay, no se muestra la lista. Nunca "Sin destinatarios".
- Separación de direcciones: `;` siempre separa; `,` sólo si el tramo ya tiene `@` o `>` (no parte "Pérez, Ana").
- Cuerpo: `tidyText` unifica saltos de línea, quita espacios finales y reduce 3 o más saltos a 2. No altera palabras.
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

- 520 px o menos: asunto a 16 px y correo del remitente en su propia línea.
- 860 px o menos: tarjeta a sangre completa, sin borde ni sombra.

## Pendientes

- Render seguro de HTML (requiere sanitizador evaluado; hoy prohibido por P-05).
- Imágenes en línea del cuerpo (`cid:`); hoy aparecen como adjuntos.
- Exportar o imprimir el correo.
