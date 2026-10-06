# Arquitectura de frontend

## Objetivo

Interfaz local y responsive para abrir un correo MSG como un lector de correo normal: ver quien lo envio, leer el mensaje y descargar sus archivos. La pantalla principal usa lenguaje cotidiano y no muestra avisos sobre FAT, OLE, parser, propiedades crudas ni metadata tecnica.

## Estructura

```text
src/
  app/                 composicion y estilos globales
  components/ui/       controles reutilizables
  components/layout/   estructura compartida
  features/ingestion/  seleccion, cola y validacion de MSG
  features/message-viewer/ lector del correo
  features/attachments/ lista y descarga de adjuntos
  lib/                 contrato API, tipos y formateadores
```

## Flujo de usuario

1. `Dropzone` permite arrastrar o elegir MSG.
2. `useExtractionQueue` los analiza uno por uno y conserva archivo y resultado solo en memoria.
3. `MessageViewer` muestra tres pestanas: Resumen, Cuerpo y Adjuntos.
4. `AttachmentList` muestra cada archivo disponible con un boton Descargar.
5. Al descargar, `lib/api.ts` envia de nuevo el MSG que el navegador ya tiene en memoria y el indice del adjunto a `POST /api/messages/attachment`.
6. El navegador recibe el binario y comienza la descarga; no se guardan IDs ni resultados en el servidor.

Reenviar el archivo para una descarga es deliberado: mantiene el backend sin almacenamiento persistente entre acciones.

## Interaccion y accesibilidad

Las pestanas usan `tablist` y `tabpanel`, teclado con flechas, Home y End. Las acciones se expresan como botones, los estados de carga se anuncian y los mensajes de error son breves y accionables. En movil la bandeja se compacta sin ocultar las acciones principales.

El cuerpo se renderiza como texto en `pre`; nunca se usa `dangerouslySetInnerHTML`. Las referencias a archivos se eliminan al limpiar la sesion. No usar localStorage, IndexedDB ni analitica.

## Archivos clave

- `app/App.tsx`: compone seleccion, cola, lector y ayuda.
- `features/message-viewer/components/MessageViewer.tsx`: resumen humano, cuerpo y adjuntos; no renderiza diagnostico tecnico.
- `features/attachments/components/AttachmentList.tsx`: boton de descarga por adjunto y estado puntual.
- `lib/api.ts`: carga multipart, normalizacion de respuesta y descarga del binario temporal.
- `features/ingestion/hooks/useExtractionQueue.ts`: cola secuencial y limpieza de referencias.

## Comandos

```powershell
npm run build
npm run lint
npm test
```

En desarrollo usa `http://127.0.0.1:8000/api` por defecto. El build servido por el backend usa `/api` en el mismo origen.
