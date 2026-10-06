# SPEC-05 Visor de adjuntos

Estado: implementada
Código: `src/features/attachments/components/AttachmentViewer.tsx`, `AttachmentPreview.tsx`, `AttachmentDetails.tsx`, `lib/viewerMode.ts`, `lib/decodeText.ts`, `hooks/useAttachmentFiles.ts`, `viewer.css`
Relacionadas: SPEC-04, backend SPEC-B02, ADR-10, ADR-11

## Objetivo

Ver un adjunto de frente, a pantalla completa, sin descargarlo: imágenes, PDF, texto, vídeo, audio y la miniatura guardada por AutoCAD u Office.

## Comportamiento

- Se abre con "Ver <nombre>" desde la lista de adjuntos o desde una imagen del cuerpo, en un `<dialog>` modal nativo a pantalla completa con fondo `--viewer-backdrop`.
- Barra superior: icono de tipo, nombre, "TIPO · tamaño · i de N"; acciones Detalles (alterna), Descargar y Cerrar.
- Flechas laterales y teclas ← → pasan al adjunto anterior o siguiente (circular). Esc cierra. Al cerrar, el foco vuelve al botón que abrió el visor.
- Panel Detalles (320 px a la derecha; flotante bajo 960 px): Tipo, Tamaño y los metadatos del backend agrupados (sin repetir nombre ni tamaño).

## Modos (`viewerMode`)

- image: PNG, JPEG, GIF, WEBP, BMP, ICO, AVIF, SVG o sin extensión con MIME de imagen. `<img>` con el binario original.
- converted: TIFF, EMF, WMF, DIB o imagen que el navegador no muestra. `<img>` con el JPEG de `preview=true`.
- pdf: `<iframe>` con el visor de PDF del navegador; el binario se fuerza a `application/pdf`.
- text: TXT, CSV, LOG, JSON, XML, MD, INI, YAML, SQL, EML, HTML. `<pre>` monoespaciado con el primer MB; UTF-8 o Windows-1252.
- video: MP4, M4V, WEBM, OGV, MOV. `<video controls>`.
- audio: MP3, WAV, OGG, M4A, AAC, FLAC. `<audio controls>` en una hoja.
- embedded: DWG, DXF u Office con miniatura incrustada. La miniatura grande con la nota "Miniatura guardada dentro del archivo por el programa que lo creó…".
- none: icono grande, nombre, "No hay vista previa para este tipo de archivo." y Descargar.

## Estados

- Carga: spinner con etiqueta "Cargando vista previa".
- Éxito: el contenido según el modo.
- Error: "No se pudo mostrar la vista previa." con Descargar.
- Descarga fallida: aviso rojo bajo la barra.

## Criterios de aceptación

- CA-01: abre una imagen, navega al siguiente adjunto y al cerrar devuelve el foco. Prueba: `AttachmentList.test.tsx`.
- CA-02: sin vista previa ofrece descargar y muestra los detalles del backend. Prueba: `AttachmentList.test.tsx`.
- CA-03: la tabla de modos asigna imagen, conversión, PDF, texto, media, incrustada y ninguno. Prueba: `viewerMode.test.ts`.
- CA-04: con backend real, la imagen se muestra a su tamaño natural y Esc cierra. Prueba: `e2e/local-api.spec.ts` (visor).
- CA-05: el texto en Windows-1252 se lee con tildes. Prueba: `viewerMode.test.ts` (decodeText).
- CA-06: el visor ocupa toda la pantalla sin desborde en 320 a 1920 px. Prueba: capturas `03-visor-imagen` y `04-visor-plano` de `test:visual`.

## Seguridad

- Nada del adjunto se interpreta como HTML de la página: texto en `<pre>`, SVG sólo en `<img>`, PDF en el visor aislado del navegador.
- Las URLs `blob:` se crean una vez por adjunto y variante y se revocan al cerrar el correo.

## Pendientes

- Zoom y paneo en imágenes grandes.
- Miniatura de la primera página de PDF en la tarjeta.
