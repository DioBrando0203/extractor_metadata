# Resultados de calidad (backend)

Última ejecución: 2026-10-06 00:37 -05:00 (America/Lima).
Entorno: Windows 11, Python 3.12.10 en `.venv`.

## Comandos

- `python -m pytest`: 58 pruebas aprobadas. Una advertencia de deprecación de Starlette TestClient con httpx; no afecta resultados.
- `python -m ruff check app tests`: aprobado.
- `python -m ruff format --check app tests`: 41 archivos con formato correcto.

## Verificaciones destacadas

- Miniaturas: PNG, JPEG, GIF, BMP, TIFF y WEBP; DWG con preview PNG y BMP; DXF `THUMBNAILIMAGE`; Office `docProps/thumbnail`.
- Rechazo: EPS y PDF no se decodifican como imagen; sección DWG alterada se ignora.
- Endpoint `preview=true`: TIFF a JPEG; `NO_PREVIEW` sin vista previa; temporal vacío en ambos casos.
- Presupuesto de miniaturas: omite sin cambiar estado ni advertencias.
- Refactorización: la suite previa pasa sin modificar aserciones; sólo cambiaron imports y puntos de parcheo.
- Integración: E2E del frontend (6) contra este backend reiniciado, incluida miniatura real y visor.

## No ejecutado

- Suite en Linux en esta sesión.
- MSG real del usuario con la nueva versión.
