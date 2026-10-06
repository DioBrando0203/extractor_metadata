# Componentes de adjuntos

`AttachmentList.tsx`: cabecera con total, rejilla de tarjetas descargables, plegado a partir de 6 y error de descarga. Comportamiento en SPEC-04.

- Clasificación de tipo en `../lib/fileKind.ts`.
- Descarga vía `lib/api.downloadAttachment`; el navegador reenvía el MSG en memoria (ADR-04).
- Los binarios sólo llegan al navegador al descargar. Sin vistas previas ni ejecución.
- `message-viewer` compone este componente (ADR-05).
