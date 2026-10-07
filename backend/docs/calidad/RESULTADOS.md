# Resultados de calidad (backend)

Última ejecución: 2026-10-08 22:40 -05:00 (America/Lima).
Entorno: Windows 11, Python 3.12.10 en `.venv`; y Linux (contenedor `python:3.12-slim`, Python 3.12.14, kernel 6.18 WSL2) con el mismo resultado.

## Comandos

- `python -m pytest`: 124 pruebas aprobadas. Una advertencia de deprecación de Starlette TestClient con httpx; no afecta resultados.
- `python -m ruff check app tests`: aprobado.
- `python -m ruff format --check app tests`: 70 archivos con formato correcto.

## Verificaciones destacadas

- MiniFAT perdida (PEN-04, sintético): mini stream en orden inverso y MiniFAT borrada de la cabecera; asunto igual al `Subject` de los encabezados, nombre y Content-ID reales, descarga exacta y original intacto; con el código anterior la prueba principal falla. Tabla incoherente y tablas ambiguas rechazadas.
- MSG real del usuario (sólo local) antes y después de PEN-04: la MiniFAT (8 sectores) explica 254 de 254 streams pequeños; el parser ya abre el correo; los 2 adjuntos del directorio pasan de Content-ID inferido a real con su nombre; mismos 12 adjuntos con descarga exacta; 4 imágenes en posición (2 por Content-ID real y 2 por medidas); análisis en 1,1 s.
- Linux (PEN-10, parte backend): suite completa, ruff check y ruff format aprobados antes y después de PEN-04 (120 y 124 pruebas).
- Geodatos: `.kml`/`.kmz` sólo entran por la ruta temporal; extensión inválida, KMZ sin KML y GDAL ausente se rechazan con código seguro y sin temporales. Con GDAL 3.12.2 instalado, KML sintético devuelve ZIP con `prueba.gpkg` y cabecera SQLite válida.
- Rescate ampliado (sintético): JPEG, GIF, DOCX y PDF sueltos; truncados rechazados; miniatura EXIF e imagen dentro de un DOCX no duplicadas; adjunto pequeño sin entrada en el mini stream rescatado; firma borrada repuesta en copia; cabecera destruida con sobre y adjunto descargado con bytes exactos.
- MSG real del usuario (sólo local) antes y después de PEN-03: mismos 12 adjuntos (9 PNG y 1 PDF recuperados, con los mismos tamaños), mismo sobre y cuerpo; el PDF recuperado pasa de 2 635 579 a 2 635 581 bytes porque ahora conserva el fin de línea CRLF final que sigue a `%%EOF` (los bytes siguientes son relleno). Análisis en 1,6 s.

- Correos adjuntos: lectura con el mismo flujo (parser y respaldo OLE), tres niveles, límites de profundidad y cantidad, stream dañado marcado como parcial, descarga como `.msg` legible y de adjuntos internos con `message_path`; el temporal queda vacío.
- EML y MSG adjuntos como archivo: sobre, cuerpo con imagen en posición, correo dentro del EML, descargas por `message_path` dentro del EML y del `.msg`; un `.doc` y un `.eml` sin encabezados siguen como archivos.
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
