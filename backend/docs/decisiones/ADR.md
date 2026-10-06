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
