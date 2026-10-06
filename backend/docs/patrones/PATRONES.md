# Patrones de diseño (backend)

Catálogo de patrones en uso: dónde están, cuándo aplicarlos y cuándo no. Antes de crear una estructura nueva, reutilizar una de estas.

## Strategy con registro

Dónde: `metadata/extractor.py` (`NATIVE_EXTRACTORS`, `NativeExtractor`).
Qué: cada formato es una función con firma común; un registro decide cuál aplica.
Cuándo: varias variantes intercambiables de un mismo paso (formatos, modos de vista previa).
Cómo extender: nuevo módulo y una línea en el registro. No añadir `if formato == ...` en la lógica común.

## Estrategias de lectura con contexto compartido

Dónde: `msg/reader.py` (`_parsed_message`, `_recovered_message`, `_ReadContext`).
Qué: dos formas de obtener el correo (parser completo o recuperación OLE) que comparten datos y cierre.
Cuándo: un proceso con camino principal y camino de respaldo.

## Cadena de respaldo (Chain of fallbacks)

Dónde: `msg/envelope.py` (`Envelope.complete_with`), `reader._ReadContext.fallback_envelope`.
Qué: varias fuentes del mismo dato en orden de confianza; cada campo vacío se completa con la primera fuente que lo tenga.
Cuándo: un dato puede venir de varias partes del archivo con distinta resistencia al daño.
Regla: sólo fuentes reales del archivo; las deducciones van aparte y se marcan como tales.

## Fachada de paquete

Dónde: `msg/__init__.py`, `metadata/__init__.py`, `previews/__init__.py`.
Qué: el paquete expone una API mínima; los módulos internos pueden reorganizarse sin romper a quien lo usa.
Regla: PY-09. Las pruebas pueden importar módulos internos para parchear dependencias.

## Parameter Object

Dónde: `_ReadContext` (reader), `_IsolatedJob` (worker), `OleMetadata` (ole_reader).
Qué: agrupa datos que viajan juntos con nombres explícitos.
Cuándo: más de 5 parámetros o tuplas de más de 2 elementos (PY-03, PY-12).

## Proceso aislado (Sandbox)

Dónde: `worker.py` (`_run_isolated`, `_respond`, `_harden_child`, `_reap`).
Qué: el parseo de archivos no confiables corre en un hijo con plazo, memoria acotada y salida sólo JSON.
Cuándo: todo código que interprete bytes del usuario con librerías de terceros.

## Gestor de contexto para recursos efímeros

Dónde: `fat_recovery.recovered_ole_path`, `TemporaryDirectory` en rutas, `with` en streams OLE.
Qué: garantiza la limpieza aunque haya excepción.
Cuándo: siempre que se cree un temporal, se abra un archivo o un contenedor.

## Tolerancia por elemento (Bulkhead)

Dónde: `attachments.py`, `ole_reader._read_stream_item`, `reader._fixed_properties`.
Qué: un adjunto o propiedad ilegible produce una advertencia y no detiene el resto.
Cuándo: listas de elementos independientes dentro de un archivo dañado.

## Presupuesto (Budget)

Dónde: `limits.limit_response`, `ATTACHMENT_BUDGET_SECONDS`, `exiftool._external_timeout`.
Qué: límites globales de tiempo y tamaño que degradan con elegancia (se omiten miniaturas, no se falla).
Cuándo: trabajo opcional que podría crecer sin control.

## Funciones puras en el núcleo

Dónde: `previews/embedded.py`, `metadata/detection.py`, `msg/names.py`, `msg/text.py`.
Qué: reciben bytes o valores y devuelven valores; se prueban sin archivos ni red.

## Antipatrones prohibidos

- Módulos `utils.py` o `helpers.py` genéricos: cada utilidad va junto a su dominio.
- Funciones "Dios" de más de 60 líneas que mezclan lectura, decisión y armado de respuesta.
- Copiar y pegar el ciclo de vida de un proceso, un temporal o una lectura por bloques: extraer.
- `if/elif` por formato en lógica común en lugar de registrar una estrategia.
- Banderas booleanas que cambian por completo lo que hace una función; preferir dos funciones o una estrategia.
- Capturar `Exception` para ocultar errores de programación en lugar de fronteras de tolerancia.
- Herencia para reutilizar código; preferir composición y funciones.
