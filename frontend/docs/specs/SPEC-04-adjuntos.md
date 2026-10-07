# SPEC-04 Datos adjuntos en el lector

Estado: implementada
Código: `src/features/attachments/` (`AttachmentList`, `AttachmentTiles`, `FileTypeIcon`, `lib/fileKind.ts`, `hooks/useAttachmentFiles.ts`)
Relacionadas: SPEC-03, SPEC-05, backend SPEC-B02, ADR-04, ADR-10

## Objetivo

Ver de frente las imágenes, planos y portadas de documentos sin descargarlos, y descargar cualquier adjunto con un clic, como en Outlook.

## Comportamiento

- Cabecera: clip, "N datos adjuntos" y tamaño total; "Descargar todo" (ZIP del backend, `DownloadAllButton`) si hay dos o más adjuntos que no son enlaces; "Mostrar los N" / "Mostrar menos" si hay más de 6.
- En la pestaña Mensaje se listan sólo los adjuntos no incrustados en el cuerpo; la pestaña Datos adjuntos muestra todos, sin plegado, con el título "Todos los datos adjuntos (N)" (ADR-13).
- Orden visual: primero los adjuntos con miniatura, después el resto, conservando el orden original dentro de cada grupo. El índice que se envía a la API es siempre la posición original.
- Con miniatura (`preview`): tarjeta con la imagen (16:10; `cover` para fotos, `contain` para miniaturas incrustadas), icono de tipo, nombre y "TIPO · tamaño".
- Sin miniatura: chip con icono de tipo coloreado, nombre, tipo y tamaño.
- Toda tarjeta o chip es un botón "Ver <nombre>" que abre el visor (SPEC-05). Un correo adjunto legible es "Abrir <nombre>" y se abre en el lector (SPEC-03).
- Correo adjunto (`kind: 'message'`): icono de correo y "Correo · tamaño", aunque su asunto parezca tener extensión; se descarga como vino (`.msg` o `.eml`).
- Enlace (`kind: 'link'`): icono del tipo de archivo, "TIPO · Enlace web" o "TIPO · Carpeta compartida" y sin botón de descarga, porque sus bytes no viajan en el correo.
- Cada adjunto tiene un botón "Descargar <nombre>": siempre visible en chips y en táctil; en tarjetas aparece al pasar el ratón o al enfocar.
- Descarga: spinner en el botón mientras se prepara; se pueden descargar varios a la vez; el binario se reutiliza si ya se pidió para el visor.
- Error de descarga: `role="alert"` bajo la lista con el nombre del adjunto.

## Clasificación (`fileKind`, `kindLabel`)

- Por extensión primero; si falta, por MIME.
- Grupos: pdf, word, excel, slides, image, cad, archive, mail, text, media, other.
- `describeAttachment` y `attachmentMeta` aplican primero `kind`: un correo adjunto siempre es mail.
- Etiqueta: extensión en mayúsculas o, sin extensión, descripción ("Imagen", "Archivo").

## Estados

- Carga: botón de descarga con spinner.
- Vacío: la sección no se muestra.
- Éxito: tarjetas o chips; descarga con el nombre de `Content-Disposition`.
- Parcial: sin tamaño se muestra "—"; sin miniatura, chip.
- Error: alerta; el botón vuelve a estar disponible.

## Criterios de aceptación

- CA-01: una imagen con miniatura muestra la imagen y un archivo sin miniatura muestra un chip con descarga. Prueba: `AttachmentList.test.tsx`.
- CA-02: pulsar Descargar baja los bytes correctos con su nombre. Prueba: `e2e/local-api.spec.ts`.
- CA-03: con 9 adjuntos se ven 6 y se pueden ver todos. Prueba: `MessageViewer.test.tsx`.
- CA-04: la clasificación prioriza extensión y cae al MIME. Prueba: `fileKind.test.ts`.
- CA-05: miniatura real generada por el backend para un PNG adjunto. Prueba: `e2e/local-api.spec.ts` (visor).
- CA-06: a 320 px el botón de descarga es visible sin desborde. Prueba: `e2e/local-api.spec.ts` (móvil).
- CA-07: un enlace muestra dónde vive y no ofrece descarga. Prueba: `MessageReader.test.tsx`, `fileKind.test.ts`, `link.test.ts`, `e2e/local-api.spec.ts`.
- CA-08: un correo adjunto se etiqueta como Correo aunque su asunto tenga puntos. Prueba: `fileKind.test.ts`.
- CA-09: "Descargar todo" baja un ZIP con el nombre del MSG, avisa si falla y no aparece con un solo archivo descargable. Prueba: `AttachmentList.test.tsx`, `lib/api.test.ts`, `e2e/local-api.spec.ts`.

## Pendientes

- Ocultar imágenes en línea de firmas (`cid:`).
