# Guía operativa para agentes IA (backend)

Protocolo obligatorio para cualquier IA que modifique `backend/`. Si contradice una instrucción explícita del usuario, gana el usuario y se registra en la bitácora.

## Contexto mínimo

- Servicio FastAPI que por defecto sólo escucha en 127.0.0.1; el acceso LAN es opcional y explícito (ADR-B12). Lee MSG que el navegador envía y responde JSON o un binario.
- Sin base de datos, sesiones, cuentas, nube, telemetría ni logs con contenido de correos.
- Cada solicitud trabaja en un temporal propio que se borra al terminar, también ante error o timeout.
- El MSG original nunca se modifica. Una reparación sólo ocurre en una copia temporal.
- El parseo ocurre en un proceso hijo aislado con plazo; el proceso principal nunca interpreta el archivo.

## Flujo de trabajo (SDD)

1. Entender: leer la spec y el código real del paquete afectado.
2. Especificar: actualizar o crear la spec con criterios de aceptación verificables (CA-xx).
3. Diseñar: ubicar el cambio según "Dónde va cada cosa"; elegir patrón en `patrones/PATRONES.md`.
4. Implementar: respetar PY-xx; funciones cortas; sin duplicar lógica existente.
5. Probar: prueba sintética que falle antes del cambio y pase después (C-12 del frontend aplica igual).
6. Verificar: comandos de la sección Verificación.
7. Registrar: resultados, bitácora y, si aplica, bloqueos y ADR.

## Definición de terminado

- `pytest`, `ruff check` y `ruff format --check` pasan.
- Ningún módulo nuevo o modificado supera 300 líneas ni una función 60 (PY-01, PY-02).
- Spec, `ARQUITECTURA.md` y `estilos/API.md` reflejan el contrato real.
- Si cambió el contrato: tipos y normalización del frontend actualizados y E2E ejecutado.
- Bitácora con hora America/Lima y evidencia real.

## Prohibiciones

- No escribir código con secuencias de escape dentro de heredocs de shell: se convierten en caracteres reales (B-13 del frontend). Usar el editor o un archivo de script.
- No escribir sobre el archivo recibido ni fuera del directorio temporal de la solicitud.
- No persistir correos, adjuntos, metadatos, rutas ni nombres en disco, logs o caché.
- No ejecutar macros, HTML, scripts ni comandos construidos con datos del usuario; nunca `shell=True`.
- No abrir con Pillow formatos fuera de la lista cerrada de `previews/render.py` (EPS invocaría Ghostscript).
- No eliminar límites de tamaño, tiempo o memoria para que un archivo "funcione".
- No devolver trazas, rutas temporales ni bytes de adjuntos dentro del JSON (salvo miniaturas acotadas).
- No afirmar reparación física ni interpretación profunda de DWG.
- No agregar correos reales como fixtures; usar `tests/msg_factory.py` y archivos generados en la prueba.

## Dónde va cada cosa

- Ruta HTTP nueva o parámetro: `app/api/routes/`. Sólo coordina: validar, copiar a temporal, llamar al worker, responder.
- Ejecución aislada, plazos y respuesta JSON del hijo: `app/services/worker.py`.
- Lectura del contenedor MSG: `app/services/msg/` (ver mapa en `msg/__init__.py`).
- Cómo viaja un adjunto (método MAPI, referencia, correo adjunto): `msg/attachment_entries.py`; abrir correos adjuntos: `msg/embedded.py` (ADR-B13).
- Metadatos de un formato nuevo: módulo en `app/services/metadata/` y registro en `extractor.py` (Strategy).
- Miniaturas: `app/services/previews/` (`embedded.py` localiza, `render.py` convierte).
- Contrato JSON: `app/models/schemas.py`.
- Límites y presupuestos: `app/core/config.py`.

## Cómo añadir un formato de adjunto

1. Detectarlo por firma en `metadata/detection.py` (nunca sólo por extensión).
2. Crear `metadata/<formato>.py` con `def <formato>_metadata(payload, detected) -> ExtractionResult`.
3. Registrar un `NativeExtractor` en `metadata/extractor.py`.
4. Si el formato guarda miniatura, leerla en `previews/embedded.py` y añadir su caso a `embedded_thumbnail`.
5. Pruebas con un archivo sintético válido y uno corrupto en `tests/`.

## Verificación

Desde `backend/` (Windows: `.venv/Scripts/python.exe`; Linux: `.venv/bin/python`):

- `python -m pytest`
- `python -m ruff check app tests`
- `python -m ruff format --check app tests`
- Si cambió el contrato: `npm run build && npm run test:e2e` desde `frontend/`.

Un servidor ya iniciado no recarga código: reiniciarlo antes de probar el flujo HTTP (B-09).
