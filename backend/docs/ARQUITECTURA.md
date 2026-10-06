# Arquitectura del backend

## Objetivo

Servicio local para abrir correos MSG, mostrar lo que se pueda leer y entregar sus archivos adjuntos. La prioridad es una experiencia clara para quien solo quiere ver su correo y descargar sus documentos. No usa base de datos, cuentas, nube, telemetria ni historial.

El archivo MSG original nunca se modifica. Cada solicitud trabaja con una copia temporal y la elimina al terminar, tambien ante errores o timeout.

## Componentes

```text
app/
  main.py                         API local y frontend compilado
  api/routes/messages.py          carga, extraccion y descarga temporal
  core/config.py                  configuracion y presupuestos
  core/middleware.py              host y Origin locales
  core/errors.py                  errores seguros
  models/schemas.py               contrato del correo y adjuntos
  services/worker.py              proceso aislado y timeout proporcional al peso
  services/message_extractor.py   lectura MSG/OLE y recuperacion parcial
  services/file_metadata.py       reconocimiento opcional por formato
tests/                            MSG y adjuntos sinteticos, sin correos privados
```

## Flujo

1. El navegador envia un MSG mediante multipart.
2. La API lo copia por bloques a un directorio temporal con nombre corto.
3. Un proceso aislado valida OLE/MAPI, lee el correo y enumera adjuntos.
4. La respuesta devuelve solo informacion del correo, no bytes de adjuntos.
5. Al pulsar Descargar, el navegador reenvia el MSG que conserva en memoria junto con el indice del adjunto.
6. Otro directorio temporal extrae solo ese archivo, lo envia como descarga y se borra despues de transmitirlo.

El trabajo pesado no ocupa el event loop. El timeout crece con el tamano del MSG y no existe un rechazo fijo por peso del correo o de los adjuntos. En Linux el proceso usa limite de memoria virtual; Windows conserva aislamiento y timeout.

## Contrato local

- `GET /api/health`: disponibilidad sin almacenamiento.
- `POST /api/messages/extract`: multipart `file` con un `.msg`; devuelve el correo, texto disponible y lista de adjuntos.
- `POST /api/messages/attachment`: multipart `file` y `attachment_index`; devuelve el binario del adjunto con descarga. No entrega rutas, IDs ni crea sesiones persistentes.
- Errores: `415` para tipo incorrecto, `422` para lectura no posible y `403` para origen externo.

La descarga vuelve a recibir el MSG a proposito: asi no se conserva ningun correo ni adjunto en el servidor entre acciones.

## Lectura y recuperacion

Se reconoce la firma antes de interpretar contenido. El lector intenta el parser MSG normal y conserva texto, encabezados y adjuntos legibles aunque una parte falle. Para una tabla FAT/DIFAT truncada que pueda verificarse, se corrige solo una copia efimera para leer streams que aun existen. Esto no repara el archivo original ni promete recuperar bytes perdidos.

Los adjuntos se extraen por indice directamente desde OLE, uno a uno, para que una descarga pueda conservar sus bytes aunque la lectura detallada de metadata no este disponible. Si una FAT recuperada deja datos continuos fuera de los enlaces OLE, se validan firmas PNG/PDF completas y se agregan solo como archivos recuperados; el mismo indice permite descargarlos. Se respetan los nombres cuando existen y se detectan firmas comunes para nombres sin extension. No se ejecutan macros ni HTML.

## Seguridad y continuidad

Solo escucha en loopback. Host y Origin externos se bloquean antes de procesar multipart. No se registran contenidos de correos. Los temporales se limpian en exito, error y timeout; un apagado abrupto puede impedir cualquier `finally`, por lo que no se afirma una garantia imposible.

Desde `backend` en Windows:

```powershell
.venv\Scripts\python.exe -m pytest
.venv\Scripts\python.exe -m ruff check app tests
.venv\Scripts\python.exe -m ruff format --check app tests
```

Actualizar `REQUERIMIENTOS.md`, calidad, bloqueos y bitacora junto con cambios de contrato o comportamiento.
