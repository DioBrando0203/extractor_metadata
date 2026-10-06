# Reglas de programación (Python)

Obligatorias. Citar el ID en revisiones y bitácora. Patrones concretos en `patrones/PATRONES.md`.

## Tamaño y responsabilidad

- PY-01: un módulo de `app/`, una responsabilidad. Máximo 300 líneas. En `tests/`, un archivo por módulo o paquete probado. Al acercarse a 250, dividir por responsabilidad en un paquete con `__init__.py` como fachada.
- PY-02: una función hace una cosa. Objetivo 30 líneas; máximo 60. Si necesita comentarios de "paso 1, paso 2", extraer funciones con nombre.
- PY-03: máximo 5 parámetros. Con más, agrupar en un `@dataclass` (Parameter Object), como `_ReadContext` o `_IsolatedJob`.
- PY-04: máximo 3 niveles de indentación dentro de una función. Usar retornos tempranos (guard clauses).
- PY-05: el nombre del módulo dice qué contiene (`fat_recovery.py`, no `utils.py` ni `helpers.py`).

## Reutilización

- PY-06: antes de escribir una función, buscar si existe (`rg "def nombre"`); ampliar la existente si encaja.
- PY-07: regla de tres: la segunda copia se tolera, la tercera obliga a extraer. Ejemplo: `_run_isolated` unificó dos ciclos de proceso idénticos.
- PY-08: constantes con nombre en lugar de literales repetidos (`ATTACHMENT_DATA_STREAM`, no `"__substg1.0_37010102"` en tres archivos).
- PY-09: la API pública de un paquete se expone en su `__init__.py` con `__all__`; otros paquetes importan desde ahí, no desde módulos internos.
- PY-10: lo privado del módulo lleva prefijo `_`. Si otro módulo lo necesita, se vuelve público (sin `_`) y se documenta.

## Tipado y datos

- PY-11: anotar tipos en toda función. `X | None` en lugar de `Optional`. Sin `Any` salvo en límites con librerías no tipadas (documentar por qué).
- PY-12: datos estructurados con `@dataclass` (internos) o Pydantic (contrato HTTP). Prohibido devolver tuplas de más de 2 elementos; usar un dataclass con nombres (`OleMetadata`).
- PY-13: inmutabilidad por defecto: `@dataclass(frozen=True)` para configuración y descriptores; mutables sólo para acumuladores de resultado.
- PY-14: el contrato HTTP sólo cambia en `models/schemas.py` y se refleja en `estilos/API.md` y en `frontend/src/lib/types.ts`.

## Errores

- PY-15: errores esperables para el usuario se lanzan como `ExtractionError(mensaje_seguro, code=CODIGO)`. El mensaje está en español y no contiene rutas ni trazas.
- PY-16: `except Exception` sólo en fronteras de tolerancia (un adjunto, un stream, una propiedad) y siempre registrando una advertencia o devolviendo un resultado neutro. Nunca `except: pass` silencioso en lógica de negocio.
- PY-17: un fallo parcial no pierde el resto: cada adjunto, stream y propiedad se lee de forma aislada.
- PY-18: re-lanzar con `from error` para conservar la causa; `from None` sólo cuando la causa expondría detalles internos.

## Recursos y seguridad

- PY-19: todo archivo, proceso o temporal se abre con `with` o se libera en `finally`.
- PY-20: todo procesamiento de datos del usuario tiene límite de bytes, de tiempo o ambos, declarado como constante o en `Settings`.
- PY-21: subprocesos sin `shell=True`, con argumentos constantes y datos por stdin.
- PY-22: no confiar en la extensión: detectar formato por firma antes de interpretar.
- PY-23: decodificadores de terceros sólo con lista cerrada de formatos (Pillow `formats=`), nunca autodetección abierta.
- PY-24: leer por bloques (1 MiB) los archivos grandes; no cargar el MSG completo salvo que el parser lo requiera.

## Funciones puras y efectos

- PY-25: separar cálculo de E/S: funciones puras (parseo, formato) reciben `bytes` o valores y devuelven valores; la E/S vive en el borde (rutas, worker, `download.py`).
- PY-26: sin estado global mutable. `settings` es inmutable; las pruebas lo reemplazan con `monkeypatch` y `dataclasses.replace`.
- PY-27: imports perezosos sólo dentro del proceso hijo o para dependencias pesadas opcionales, con comentario del motivo.

## Documentación en código

- PY-28: docstring de módulo que diga su responsabilidad y lo que no hace.
- PY-29: docstring en funciones públicas y en las privadas cuya intención no sea obvia; explicar el porqué, no repetir el código.
- PY-30: los límites de seguridad llevan comentario del riesgo que evitan.
