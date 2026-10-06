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
