# Decisiones de arquitectura (backend)

Formato: contexto, decisión, consecuencias. Una decisión sólo se reemplaza con otra que la cite.

## ADR-B01 Proceso hijo aislado por solicitud

Fecha: 2026-10-05. Estado: vigente.
Contexto: los parsers de terceros pueden colgarse o agotar memoria con archivos dañados.
Decisión: `multiprocessing` en modo `spawn`, plazo proporcional al tamaño, `RLIMIT_AS` en Linux y respuesta sólo JSON.
Consecuencias: coste de arranque por solicitud; el proceso principal nunca queda bloqueado.

## ADR-B02 Sin estado entre solicitudes

Fecha: 2026-10-05. Estado: vigente.
Contexto: no debe quedar ningún correo ni adjunto en el servidor.
Decisión: para descargar o previsualizar, el navegador reenvía el MSG y el índice.
Consecuencias: cada descarga vuelve a procesar el MSG; aceptable en loopback.

## ADR-B03 Reparación sólo en copia temporal

Fecha: 2026-10-05. Estado: vigente.
Contexto: MSG con DIFAT truncada conservan sus streams.
Decisión: reconstruir la DIFAT verificable en una copia; el original no se toca.
Consecuencias: se informa como lectura recuperada, nunca como reparación del archivo.

## ADR-B04 Strategy para metadatos por formato

Fecha: 2026-10-05. Estado: vigente.
Contexto: cada formato tiene su librería y sus límites.
Decisión: extractores con firma común registrados en `NATIVE_EXTRACTORS`; ExifTool como complemento opcional.
Consecuencias: un formato nuevo no toca la lógica común.

## ADR-B05 Miniaturas en la respuesta y vista previa grande bajo demanda

Fecha: 2026-10-05. Estado: vigente.
Contexto: el usuario quiere ver imágenes y planos de frente, no sólo iconos.
Decisión: miniatura JPEG de 480 px como data URI dentro del análisis (con presupuesto total) y `preview=true` en `/attachment` para una versión de 2048 px.
Consecuencias: la respuesta crece hasta ~8 MB en el peor caso; no se necesita estado ni endpoints de imágenes.

## ADR-B06 Lista cerrada de formatos de imagen

Fecha: 2026-10-05. Estado: vigente.
Contexto: la autodetección de Pillow incluye EPS, que invoca Ghostscript.
Decisión: `Image.open(..., formats=_ALLOWED_FORMATS)` y límite de 100 MP.
Consecuencias: formatos fuera de la lista no tienen miniatura, pero se descargan igual.

## ADR-B07 Paquetes por responsabilidad

Fecha: 2026-10-05. Estado: vigente. Reemplaza `message_extractor.py` (857 líneas) y `file_metadata.py` (633 líneas).
Contexto: archivos grandes mezclaban recuperación, lectura, adjuntos, descarga y límites; difíciles de revisar y de extender.
Decisión: paquetes `msg/`, `metadata/` y `previews/` con fachada en `__init__.py`, funciones de máximo 60 líneas y Parameter Objects (`_ReadContext`, `OleMetadata`, `_IsolatedJob`). El worker unifica el ciclo del hijo en `_run_isolated`.
Consecuencias: misma suite de pruebas sin cambiar aserciones; los tests parchean módulos internos concretos.

## ADR-B08 Miniaturas incrustadas en lugar de render

Fecha: 2026-10-05. Estado: vigente.
Contexto: renderizar DWG o páginas PDF exige motores pesados o con licencia.
Decisión: usar la miniatura que el propio archivo guarda (DWG, DXF, Office) y el visor de PDF del navegador.
Consecuencias: archivos guardados sin miniatura sólo muestran icono y detalles; queda como pendiente evaluado.

## ADR-B09 Cadena de respaldo para el sobre del correo

Fecha: 2026-10-06. Estado: vigente.
Contexto: en un MSG real con FAT dañada, el parser falla y las propiedades cortas (asunto, remitente, Para) viven en el mini stream, que queda ilegible; la app mostraba "Remitente desconocido" aunque los encabezados de transporte estaban completos.
Decisión: `Envelope.complete_with` rellena cada campo vacío en orden de confianza: parser, propiedades MAPI alternativas y encabezados de transporte (`007D`), que viven en sectores normales.
Consecuencias: remitente, asunto, destinatarios y fecha se identifican con datos reales del correo, nunca deducidos; un campo sólo cambia si estaba vacío.

## ADR-B10 Imágenes incrustadas como marcadores en el texto

Fecha: 2026-10-06. Estado: vigente.
Contexto: el usuario quiere ver las imágenes donde iban en el correo, pero el cuerpo se entrega como texto plano por seguridad (ADR-07 del frontend).
Decisión: al convertir HTML a texto, cada `<img src="cid:…">` se vuelve `[cid:…]` en su línea (convención del texto plano de Outlook) y cada adjunto expone su `content_id`. Las imágenes remotas se descartan.
Consecuencias: el frontend coloca la miniatura en su posición sin interpretar HTML. Si el daño borró HTML, RTF y nombres, no hay posición y la imagen queda sólo en la lista de adjuntos.

## ADR-B11 Cuerpo desde el RTF suelto y posición reconstruida por medidas

Fecha: 2026-10-06. Estado: vigente.
Contexto: en el MSG real del usuario, el RTF del cuerpo (con el HTML y las posiciones `cid:`) seguía entero en el archivo pero sin enlace, y los Content-ID de los adjuntos se perdieron con el mini stream.
Decisión: buscar la firma `LZFu`, aceptar el RTF sólo con CRC válido y texto coherente con el cuerpo legible, y usar su HTML. Para enlazar imágenes sin Content-ID se comparan las medidas declaradas en cada `<img>` con los píxeles de cada adjunto: tamaño exacto, o proporción (±1 %) con resolución suficiente cuando el par es inequívoco. Dos pasadas secuenciales: lo emparejado por tamaño exacto no compite después.
Consecuencias: en el MSG real se ubicaron 4 de 14 imágenes (logos de firmas); iconos repetidos y capturas con varias candidatas quedan sin posición por diseño. Cada asignación se marca `content_id_inferred` y la interfaz lo indica.

## ADR-B12 Acceso LAN opcional y explícito

Fecha: 2026-10-06. Estado: vigente. Amplía ADR-B02 y RQ-01 sin reemplazarlos.
Contexto: el usuario necesita abrir la aplicación desde otra PC de la misma red sin instalarla en cada equipo.
Decisión: Host y Origin aceptados salen de `APP_ALLOWED_HOSTS` y `APP_ALLOWED_ORIGINS` (`backend/.env`, `core/config.env_list`); sin variables se conservan los valores de loopback. El frontend apunta al servidor con `VITE_API_URL`. `iniciar.py` sigue escuchando sólo en 127.0.0.1; el modo LAN exige levantar Uvicorn y Vite con `--host 0.0.0.0` a mano (README).
Consecuencias: en modo LAN cualquier equipo que alcance el puerto puede enviar archivos al servicio; usarlo sólo en una red de confianza. Sigue sin haber cuentas, base de datos, nube ni historial, y cada solicitud conserva su temporal efímero. Los correos viajan por la red local sin cifrar (HTTP).

## ADR-B13 Correos adjuntos como MSG propio en el temporal

Fecha: 2026-10-06. Estado: vigente.
Contexto: un correo reenviado como adjunto (método 5) vive en la carpeta `__substg1.0_3701000D` de su adjunto. Todo el flujo (parser, respaldo OLE, sobre de respaldo, RTF suelto, descargas) trabaja sobre un archivo.
Decisión: copiar esa carpeta a un MSG propio con `OleWriter` de extract-msg, stream por stream (uno ilegible se omite y se avisa), con los 8 bytes reservados del stream de propiedades raíz y la tabla `__nameid_version1.0` del contenedor. La copia vive en el temporal de la solicitud, se lee con el mismo flujo y se borra al terminar. `AttachmentMetadata.message` es recursivo; las descargas internas usan `message_path`. `EmbeddedBudget` limita a 3 niveles y 20 correos por análisis y comparte el plazo de miniaturas; `limit_response` acota una sola vez toda la respuesta.
Consecuencias: cada nivel cuesta una copia en disco y en memoria del tamaño del correo interno (`OleWriter` retiene los streams). Descargar un adjunto interno vuelve a copiar cada nivel (ADR-B02). Un correo interno ilegible o fuera del presupuesto se puede descargar como `.msg`.

## ADR-B14 Adjuntos por referencia como enlace sin seguirlo

Fecha: 2026-10-06. Estado: vigente.
Contexto: los adjuntos de OneDrive o SharePoint (método 7) y los que apuntan a una ruta (2, 3, 4) no traen bytes; el correo sólo guarda la dirección (`0x370D` o `0x3708`). Antes se informaban como "anidado" o "ilegible".
Decisión: devolverlos como `kind=link` con la dirección como texto, sin advertencia porque no es un daño. El backend nunca abre la dirección (RQ-01). La interfaz decide cómo ofrecerla.
Consecuencias: no hay miniatura ni descarga; el usuario abre el enlace con su navegador y sus credenciales, fuera de esta aplicación.

## ADR-B15 EML y MSG adjuntos como archivo

Fecha: 2026-10-06. Estado: vigente. Amplía ADR-B13.
Contexto: otros clientes de correo adjuntan un reenvío como `.eml` o adjuntan un `.msg` de disco con sus bytes (método 1); antes se veían como archivos sin leer.
Decisión: un adjunto con firma CFB y streams MAPI se escribe al temporal y se lee con el mismo flujo del MSG. Un `.eml` con De, Asunto o Fecha se lee con `email` de la biblioteca estándar (`policy.default`, sin red), con el mismo contrato y las mismas reglas de cuerpo (HTML a texto con `[cid:…]`). El presupuesto pasa a `nesting.py` para que MSG y EML lo compartan; `attachments` recibe el abridor como `MessageOpener` (Protocol) y no importa a `embedded` ni a `eml`. La descarga recorre `message_path` con `_MsgSource` y `EmlSource`, que enumeran las partes en el mismo orden que el análisis.
Consecuencias: el `.eml` se detecta por extensión y encabezados; uno sin extensión queda como archivo. Un MSG dentro de un EML como archivo no se abre (raro). Sin dependencias nuevas.

## ADR-B16 Rescate ampliado con mapa de sectores

Fecha: 2026-10-06. Estado: vigente. Amplía ADR-B03.
Contexto: el rescate de datos sueltos sólo reconocía PNG y PDF y sólo tras reparar la FAT; un MSG sin firma se rechazaba entero. Buscar firmas sin más confunde una miniatura EXIF, una imagen guardada en un DOCX o un adjunto legible con adjuntos sueltos.
Decisión: registro de formatos (PNG, JPEG, GIF, PDF, ZIP/Office) validados enteros. Un candidato es suelto sólo si no cae en sectores ni mini sectores que reclama un stream alcanzable (`sector_map`), no está dentro de otro aceptado y no repite un adjunto legible. Se activa con la cabecera reparada o el parser caído; la descarga calcula lo mismo (`parser_fails`) para conservar los índices. La firma borrada con el resto de la cabecera coherente se repone en una copia; sin cabecera usable, lectura de rescate con datos validados (CRC del RTF, estructura de cada archivo, encabezados que se leen como tales).
Consecuencias: con el MSG real dañado del usuario el resultado coincide con el anterior (mismos 9 PNG y el PDF) y el PDF conserva su fin de línea. Una descarga de archivo suelto con el parser caído vuelve a probar el parser. Sin cabecera no se recuperan propiedades ni adjuntos fragmentados.

## ADR-B17 Reuniones, contactos y tareas como ItemDetails

Fecha: 2026-10-07. Estado: vigente.
Contexto: un MSG de reunión, contacto o tarea se veía como un correo sin sus datos (cuándo, dónde, quiénes). extract-msg ya abre cada clase con sus propiedades, muchas con nombre (`PSETID_Appointment`, `PSETID_Task`, `PSETID_Address`).
Decisión: un único `ItemDetails` con `kind`, fechas tipadas (para que la interfaz las muestre en la hora local), lugar y una lista ordenada de campos de texto. Cada propiedad se lee aislada y, por ser accesoria, una ilegible se omite sin volver parcial el correo. La fábrica de pruebas genera propiedades con nombre (`named_properties`).
Consecuencias: agregar un campo es una línea en una tabla. Sin el parser (MSG dañado) no hay `item`; el correo se sigue leyendo.

## ADR-B18 Correos S/MIME sin criptografía

Fecha: 2026-10-07. Estado: vigente.
Contexto: un correo firmado o cifrado se veía como un adjunto `smime.p7m` y, en los cifrados, extract-msg devolvía los bytes del PKCS#7 como si fueran el cuerpo.
Decisión: sin dependencias criptográficas. Firmado en claro (`multipart/signed`): se lee la primera parte con `email` y sus adjuntos se enumeran como en un EML, en el análisis y en la descarga. Opaco o cifrado: se reconoce por el OID al inicio del `.p7m`, se marca en `security` y el cuerpo sólo sale del stream `1000`. La firma nunca se verifica y la interfaz lo dice.
Consecuencias: no se afirma la validez de una firma ni se descifra nada. Un correo con permisos IRM (`.rpmsg`) sólo se indica como `protected`. Un correo opaco necesita Outlook para verse. `ReadContext` sale de `reader` para que el lector no pase de 250 líneas.
