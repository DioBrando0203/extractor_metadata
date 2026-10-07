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

## 2026-10-06 01:11 -05:00 Identificación del remitente y marcadores de imágenes incrustadas

Estado: terminada
Cambios: `msg/envelope.py` con cadena de respaldo (ADR-B09); `msg/parsed_fields.py` separado de `reader.py` (PY-01); `OleAttachment` con Content-ID; `content_id` en `AttachmentMetadata`; `body_text` convierte `<img src="cid:…">` en `[cid:…]` (ADR-B10); `msg_factory` admite `omit`, `headers`, `html` y `content_id`.
Evidencia: 65 pruebas aprobadas (7 nuevas en `test_envelope.py`); ruff check y format aprobados. Con el MSG real del usuario (sólo local): antes sin asunto, remitente, destinatarios ni fecha; ahora asunto con prefijo RE, remitente con correo, Para con 2 direcciones, CC con 4 y fecha.
Notas: causa raíz en B-10; límite de posiciones en B-11.

## 2026-10-06 01:32 -05:00 Cuerpo recuperado del RTF suelto y posición de imágenes por medidas

Estado: terminada
Cambios: `msg/raw_body.py` (RTF `LZFu` suelto con CRC y coherencia), `msg/inline_images.py` (emparejamiento inequívoco por medidas), `signature_offsets` público para reutilizar la búsqueda por bloques, `content_id_inferred` en el contrato.
Evidencia: 73 pruebas aprobadas (8 nuevas); ruff check y format aprobados. MSG real del usuario (sólo local): RTF de 20 738 bytes recuperado con CRC válido; texto del HTML cubre el 99,1 % de las palabras del texto plano; 16 marcadores de imagen; 4 imágenes ubicadas (2 por tamaño exacto, 2 por proporción única) y 10 ambiguas sin ubicar.
Notas: ADR-B11, B-11 mitigado, B-12 resuelto.

## 2026-10-06 01:45 -05:00 Backlog de huecos conocidos

Estado: terminada
Cambios: `REQUERIMIENTOS.md` pasa de una lista suelta a un backlog priorizado PEN-01 a PEN-11 con situación, qué hacer y criterio de terminado; punteros en `AGENTS.md` y en los índices de docs.
Evidencia: revisión del código actual (métodos de adjunto, rescate de datos sueltos, formatos de Pillow, extractores registrados) y de lo observado en el MSG real.
Notas: prioridad alta para correos adjuntos (PEN-01), adjuntos en la nube (PEN-02) y rescate ampliado (PEN-03).

## 2026-10-06 22:29 -05:00 Acceso LAN documentado (PEN-12)

Estado: terminada
Cambios: ADR-B12 (modo LAN opcional y sus riesgos); RQ-01, RQ-11, CA-08, `GUIA_IA.md`, `ARQUITECTURA.md`, `estilos/API.md` y ambos `STACK.md` reflejan Host y Origin configurables; `env_list` público con docstring; `tests/test_config.py`; PEN-12 registrado y cerrado; punteros PEN-xx en `AGENTS.md` y el índice.
Evidencia: pytest 75 aprobadas (2 nuevas); ruff check y format aprobados.
Notas: el código del modo LAN vino del commit `07a9b11`; esta tarea sólo lo documenta y prueba. `iniciar.py` sigue en 127.0.0.1.
