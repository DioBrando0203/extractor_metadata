# SPEC-B03 Conversión geográfica local

Estado: parcial
Código: `api/routes/geodata.py`, `services/kmz/`, `services/worker.py`
Relacionadas: ADR-B19, PEN-15

## Objetivo

- Convertir un archivo KML o KMZ local a GeoPackage sin conservarlo en el servidor.

## Contrato

- `POST /api/geodata/convert` recibe multipart `file` con extensión `.kml` o `.kmz`.
- Respuesta correcta: ZIP con un archivo `.gpkg` generado por GDAL.
- Respuesta inválida: 415 si la extensión no es KML/KMZ.
- Error de conversión: 422 con código seguro; nunca devuelve rutas, salida de GDAL ni trazas.

## Seguridad y recursos

- La ruta copia el archivo por bloques a `temp_root/geodata-*`.
- KML dentro de KMZ: máximo `max_geodata_bytes` y ratio de compresión de hasta `max_kmz_compression_ratio`.
- La conversión corre en el hijo aislado con el plazo proporcional al tamaño.
- El temporal se borra al acabar la descarga, en error y en timeout.
- GDAL se detecta con `APP_GDAL_BIN`, PATH o instalaciones habituales de OSGeo4W en Windows.

## Criterios de aceptación

- CA-01: una extensión ajena se rechaza con 415.
- CA-02: sin GDAL el endpoint devuelve 422 `GDAL_UNAVAILABLE` y no deja temporales.
- CA-03: con GDAL disponible, un KML sintético devuelve un ZIP con un GeoPackage.
- CA-04: un KMZ sin KML o con miembro sobredimensionado se rechaza sin invocar GDAL.

## Pendiente

- Migrar la corrección estructural KML y la generación de estilos QML del prototipo original.
- Crear la interfaz React y el selector de herramientas en Inspector MSG.
