# Bitácora (backend)

Una entrada por tarea, la más reciente al final. Formato fijo:

```text
## AAAA-MM-DD HH:MM -05:00 Título corto
Estado: terminada | parcial | bloqueada
Cambios: qué se tocó
Evidencia: comandos ejecutados y resultado real
Notas: decisiones, ADR o bloqueos relacionados
```

No se registran nombres ni contenidos de correos privados.

## 2026-10-05 18:21 -05:00 Lector local MSG y extractores de adjuntos

Estado: terminada
Cambios: servicios, API local y pruebas sintéticas.

## 2026-10-05 19:27 -05:00 Recuperar MSG con FAT truncada y retirar topes fijos de peso

Estado: terminada
Evidencia: recuperación temporal y comprobación local de adjuntos JPEG/PNG.

## 2026-10-05 20:13 -05:00 Descarga temporal de adjuntos

Estado: terminada
Evidencia: `POST /api/messages/attachment`, prueba HTTP de PDF y E2E de descarga.

## 2026-10-05 20:31 -05:00 Recuperar documentos fuera de enlaces OLE

Estado: terminada
Evidencia: PDF real de 2,635,579 bytes localizado, listado y descargado con bytes idénticos (archivo del usuario, sólo local).

## 2026-10-06 00:37 -05:00 Miniaturas, vista previa y refactorización por responsabilidad

Estado: terminada
Cambios: `previews/` con miniaturas de imágenes y de las previews incrustadas en DWG, DXF y Office (ADR-B05, ADR-B06, ADR-B08); campos `preview` y `preview_source`; parámetro `preview` en `/attachment`; metadato "Miniatura incrustada" en AutoCAD. `message_extractor.py` (857 líneas) y `file_metadata.py` (633) divididos en los paquetes `msg/` y `metadata/` con funciones cortas y Parameter Objects; `worker.py` unifica el ciclo del proceso hijo en `_run_isolated` (ADR-B07). Docs nuevos: README, GUIA_IA, specs B01 y B02, ADR, reglas PY-01 a PY-30, patrones, estilo, calidad, API y bloqueos.
Evidencia: 58 pruebas aprobadas (18 nuevas de vistas previas) sin cambiar aserciones previas; ruff check y format aprobados; E2E del frontend con el backend reiniciado aprobados.
Notas: módulo más grande tras la división, `msg/reader.py` con 266 líneas.
