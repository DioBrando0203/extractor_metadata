# Resultados de calidad (backend)

Última ejecución: 2026-10-06 23:00 -05:00 (America/Lima).
Entorno: Windows 11, Python 3.12.10 en `.venv`.

## Comandos

- `python -m pytest`: 91 pruebas aprobadas. Una advertencia de deprecación de Starlette TestClient con httpx; no afecta resultados.
- `python -m ruff check app tests`: aprobado.
- `python -m ruff format --check app tests`: 51 archivos con formato correcto.

## Verificaciones destacadas

- Correos adjuntos: lectura con el mismo flujo (parser y respaldo OLE), tres niveles, límites de profundidad y cantidad, stream dañado marcado como parcial, descarga como `.msg` legible y de adjuntos internos con `message_path`; el temporal queda vacío.
- Adjuntos por referencia: URL de SharePoint, ruta de red y referencia sin dirección; sin descarga vacía.
- Integración: E2E del frontend (7) con el backend iniciado con el código actual.

- Miniaturas: PNG, JPEG, GIF, BMP, TIFF y WEBP; DWG con preview PNG y BMP; DXF `THUMBNAILIMAGE`; Office `docProps/thumbnail`.
- Rechazo: EPS y PDF no se decodifican como imagen; sección DWG alterada se ignora.
- Endpoint `preview=true`: TIFF a JPEG; `NO_PREVIEW` sin vista previa; temporal vacío en ambos casos.
- Presupuesto de miniaturas: omite sin cambiar estado ni advertencias.
- Sobre de respaldo: remitente, asunto, Para y fecha desde encabezados de transporte con el parser caído; SMTP preferido sobre direcciones Exchange.
- Imágenes incrustadas: `<img src="cid:…">` como marcador en posición, imágenes remotas descartadas, Content-ID en el adjunto.
- MSG real del usuario (sólo local): sobre completo recuperado de los encabezados de transporte.
- RTF suelto y posición por medidas: CRC, coherencia, tamaño exacto, proporción única, ambigüedad rechazada; en el MSG real 4 imágenes ubicadas y 10 ambiguas sin ubicar.
- Refactorización: la suite previa pasa sin modificar aserciones; sólo cambiaron imports y puntos de parcheo.

## No ejecutado

- Suite en Linux en esta sesión.
- Linux en esta sesión (el MSG real del usuario sí se verificó en Windows).
