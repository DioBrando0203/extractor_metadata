# Resultados de calidad

Registro: 2026-10-05 18:21:49 -05:00 (America/Lima).

| Comprobación | Resultado |
|---|---|
| pytest backend | 38 pruebas aprobadas. |
| Ruff lint y formato | Correctos, 20 archivos de código/prueba. |
| pip check | Sin dependencias incompatibles. |
| Carga grande real | MSG sintético con adjunto DWG de 11 MB procesado; advertencia >10 MB. |
| Memoria y timeout | Proceso aislado; timeout probado; tamaño del adjunto comprobado antes de carga. |
| Corrupción | Archivo no OLE rechazado; recuperación si falla parser; stream defectuoso conserva el resto. |
| Seguridad | Host/Origin externos bloqueados; límite multipart sin Content-Length probado. |
| Limpieza | Directorios de cada análisis vacíos tras éxito/errores; sin archivos en temporal después de pruebas. |
| Formatos | Imagen EXIF, PDF/XMP, OOXML, DXF y DWG básico; degradación genérica y ZIP sospechoso. |
| Codificación | MSG ANSI cp932 (japonés) conserva asunto/cuerpo y metadata raw. |
| ExifTool | Argumentos sólo lectura, stdout 1 MiB, timeout y presupuesto global con retorno nativo. |

Entorno real: Linux, Python 3.14.4, extract-msg 0.56.1, FastAPI 0.142.2. Versiones en requirements.lock.
Las pruebas generan CFB v4 propios y archivos sintéticos; no contienen correos privados.
Hay una advertencia de deprecación de Starlette/TestClient respecto a httpx; no falla la suite.
ExifTool no está instalado en esta máquina; el adaptador fue probado con procesos simulados.
No se ha validado Windows nativamente ni recuperación de todo tipo de corrupción física.
