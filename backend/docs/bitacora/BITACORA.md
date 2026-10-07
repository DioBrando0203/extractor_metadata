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

## 2026-10-06 22:42 -05:00 Correos adjuntos y adjuntos en la nube (PEN-01 y PEN-02, backend)

Estado: terminada (backend; frontend en su bitácora)
Cambios: `msg/attachment_entries.py` (método de adjunto 0x3705, dirección 0x370D/0x3708, nombre con respaldo 3001/3704); `msg/embedded.py` (correo adjunto a MSG propio con `OleWriter`, `EmbeddedBudget`); `attachments.py` clasifica antes de leer bytes (`AttachmentSources`, `without_bytes`) y divide funciones largas; `reader.py` lee recursivamente y acota una sola vez; `limits.py` recorre correos adjuntos; `download.py` con `message_path` y descarga `.msg`; ruta `/attachment` con `message_path` y `AttachmentRequest` en el worker; contrato `kind`, `link`, `message`; fábrica de MSG con `message_streams`, `attached_message` y `reference_attachment`.
Evidencia: pytest 91 aprobadas (16 nuevas en `test_embedded.py`); ruff check y format aprobados. Con el código anterior, 13 de las 16 nuevas fallan (las 3 restantes son rechazos de `message_path` que antes daban 422 por otro motivo).
Notas: ADR-B13 y ADR-B14; SPEC-B01 CA-17 a CA-21; SPEC-B02 CA-08 a CA-11. EML adjunto sigue pendiente dentro de PEN-01.

## 2026-10-06 23:09 -05:00 EML y MSG adjuntos como archivo (cierre de PEN-01)

Estado: terminada
Cambios: `msg/eml.py` (lectura con la biblioteca estándar y `EmlSource`), `msg/nesting.py` (presupuesto común y `open_nested`), `embedded.AttachedMessages` (carpeta OLE, `.msg` y `.eml` adjuntos), `attachments.MessageOpener` (Protocol) para no crear ciclos, `download.py` recorre `message_path` con `_MsgSource` y `EmlSource`, `names.message_filename`. Frontend: el visor ofrece "Descargar correo" en lugar de "Descargar .msg".
Evidencia: pytest 95 aprobadas (4 nuevas en `test_eml.py`; 3 fallan con el código anterior, la cuarta es el caso negativo); ruff check y format aprobados; frontend 75 unitarias, lint, build y format:check aprobados.
Notas: ADR-B15; SPEC-B01 CA-22 y CA-23; SPEC-B02 CA-12; PEN-01 terminada.

## 2026-10-06 23:40 -05:00 Destino visible de los enlaces (PEN-08, paso inmediato)

Estado: terminada
Cambios: `body_text.py` conserva el destino de cada enlace http/https como `texto <url>` salvo que el texto ya sea la dirección; `mailto:` y `javascript:` no se agregan.
Evidencia: pytest 97 aprobadas (2 nuevas en `test_body_text.py`, que fallan con el código anterior); ruff check y format aprobados.
Notas: SPEC-B01 CA-24; PEN-08 queda parcial (HTML saneado pendiente de decisión). La coincidencia del RTF suelto con el texto plano mejora cuando éste empieza con un enlace.

## 2026-10-06 23:57 -05:00 Rescate de datos sueltos ampliado (PEN-03)

Estado: terminada
Cambios: `raw_formats.py` (registro: ZIP/Office por EOCD coherente, PDF hasta su propio `startxref` sin pasar a otro PDF y con su fin de línea) y `raw_images.py` (PNG, JPEG con segmentos y decodificación, GIF por bloques); `sector_map.py` (sectores y mini sectores de streams alcanzables); `raw_recovery.loose_candidates` con exclusión por sectores, anidamiento y duplicado; activación también con el parser caído (`reader.parser_fails` en la descarga); `fat_recovery` repone la firma borrada en copia (`readable_container`); `rescue.py` lee sin cabecera (sueltos, RTF del cuerpo y encabezados UTF-16); `metadata` exporta `zip_kind`.
Evidencia: pytest 107 aprobadas (10 nuevas en `test_raw_recovery.py` y `test_rescue.py`; con el código anterior fallan, y la del mini stream falla simulando el mapa grueso); ruff check y format aprobados. MSG real del usuario (local): mismo resultado que antes de PEN-03 salvo el fin de línea del PDF; la primera versión del mapa marcaba todo el mini stream y perdía 2 PNG pequeños, corregido con mini sectores.
Notas: ADR-B16; SPEC-B01 CA-25 a CA-30.

## 2026-10-07 00:10 -05:00 Reuniones, contactos y tareas (PEN-07, backend)

Estado: terminada
Cambios: contrato `ItemDetails` y `MessageMetadata.item`; `msg/item_details.py` (tipo por clase de mensaje, fechas, lugar y campos en tablas, lectura aislada sin advertencias); la fábrica genera clase de mensaje, textos MAPI extra y propiedades con nombre (`named_properties`).
Evidencia: pytest 111 aprobadas (4 nuevas en `test_item_details.py`, que fallan con el contrato anterior); ruff check y format aprobados.
Notas: ADR-B17; SPEC-B01 CA-31 y CA-32; RQ-14.

## 2026-10-07 00:24 -05:00 Correos S/MIME y con permisos (PEN-06, backend)

Estado: terminada
Cambios: `msg/smime.py` (firmado en claro con su contenido MIME, opaco y cifrado por OID, IRM por `.rpmsg`); `ReadContext` sale de `reader` a `read_context.py` con los adjuntos del contenido firmado y el cuerpo S/MIME (sin los bytes del PKCS#7 que extract-msg tomaba como texto); descarga coherente en `_MsgSource`; `eml.read_parts` y `eml.body_text` públicos; contrato `security`.
Evidencia: pytest 116 aprobadas (5 nuevas en `test_smime.py`; con el código anterior fallan); ruff check y format aprobados.
Notas: ADR-B18; SPEC-B01 CA-33 y CA-34; RQ-15. La firma no se verifica (límite honesto).

## 2026-10-07 00:35 -05:00 Descargar todos los adjuntos en un ZIP (PEN-11, parte)

Estado: terminada
Cambios: `msg/archive.py` (`extract_all_attachments`); `download.open_source` con fuentes que saben contarse (`_MsgSource`, `EmlSource`, `_RescueSource`) y caché de firmado y sueltos; worker `run_archive_extraction`; ruta `POST /api/messages/attachments` y entrega común `_deliver` para `/attachment` y `/attachments`.
Evidencia: pytest 119 aprobadas (3 nuevas en `test_archive.py`); ruff check y format aprobados.
Notas: SPEC-B02 CA-13. Los enlaces se omiten; nombres repetidos numerados.

## 2026-10-07 00:50 -05:00 Documentación de cierre, nombre de descarga entre orígenes y ejemplos

Estado: terminada
Cambios: CORS expone `Content-Disposition` (PEN-13); `tests/generar_ejemplos.py` escribe los 8 MSG sintéticos de la guía; README principal con funciones nuevas, acceso por red servido desde el puerto 8000, correos de prueba y límites; resumen del backlog con PEN-13 y PEN-14; bloqueos B-14 y B-15; `AGENTS.md` con modo LAN opcional, ejemplos y B-13.
Evidencia: pytest 120 aprobadas (la nueva de PEN-13 falla con el código anterior); ruff check y format aprobados; los 8 ejemplos se analizaron por HTTP contra el servidor en marcha. Modo LAN verificado en una PC con Windows: `/api/health` y análisis completo por la IP de red, interfaz servida en el puerto 8000 y regla de firewall de entrada vigente para el Python que escucha.
Notas: falta probar en Linux (PEN-10) y desde otra PC física.

## 2026-10-08 22:05 -05:00 Backend en Linux (PEN-10, parte)

Estado: parcial
Cambios: ninguno de código; comando documentado en `PLAN_CALIDAD.md` (contenedor `python:3.12-slim`, `backend/` en sólo lectura copiado dentro, `pip install -c requirements.lock`).
Evidencia: Linux 6.18.33.2-microsoft-standard-WSL2, Python 3.12.14: pytest 120 aprobadas, ruff check aprobado, ruff format 68 archivos correctos.
Notas: no hay distro WSL propia; se usó Docker Desktop. Faltan E2E del frontend en Linux y el corpus autorizado (depende del usuario).

## 2026-10-08 22:40 -05:00 MiniFAT perdida repuesta en copia (PEN-04)

Estado: terminada
Cambios: `msg/minifat_recovery.py` (cadenas de la FAT con forma de MiniFAT, validación contra cada stream pequeño, unicidad); `fat_recovery.recovered_ole_path` repone inicio y cantidad en la copia con aviso; `parsed_fields.read_inline_tags` y `reader` ubican por medidas los sueltos también con el parser abierto; `INFERRED_POSITIONS_NOTICE` común; fábrica `build_cfb(scatter=True)`; `tests/test_minifat_recovery.py`.
Evidencia: pytest 124 aprobadas en Windows y en Linux (4 nuevas; la principal falla con el código anterior); ruff check y format aprobados. MSG real (local): diagnóstico estructural (MiniFAT en fin de cadena y 0 en la cabecera; 8 sectores encadenados en la FAT; mini stream con 119 de 128 sectores alcanzables), 254 de 254 cadenas válidas, asunto y remitente iguales a los encabezados, 12 adjuntos con descarga exacta.
Notas: ADR-B19; B-16; SPEC-B01 CA-35 y CA-36. Sin cambio de contrato: sólo un aviso nuevo.

## 2026-10-08 23:14 -05:00 Cierre momentáneo del proyecto

Estado: terminada
Cambios: "Estado del proyecto" en `REQUERIMIENTOS.md`, `AGENTS.md` y README principal.
Evidencia: decisión del usuario; última verificación en `calidad/RESULTADOS.md` (124 pruebas en Windows y Linux, ruff aprobado).
Notas: abiertos al cierre: PEN-05, PEN-09, PEN-14; parciales PEN-08 (decisión), PEN-10 (E2E en Linux y corpus) y PEN-11 (DWG, instalador, EMF fuera de Windows). La app no se abrió en el navegador en esta sesión; el único cambio visible es un aviso de texto nuevo.

## 2026-10-07 10:09 -05:00 Endpoint geodatos KML/KMZ (PEN-15)

Estado: parcial
Cambios: `POST /api/geodata/convert`; paquete `services/kmz` para extraer KMZ con límites y llamar a GDAL dentro del hijo aislado; ZIP temporal de descarga; límites de geodatos, SPEC-B03, ADR-B19 y contrato API.
Evidencia: `python -m pytest` con 123 aprobadas; `ruff check app tests` y `ruff format --check app tests` aprobados; nuevas pruebas para extensión, KMZ sin KML, GDAL ausente y limpieza; HTTP local tras reiniciar: KML sintético devuelve 422 `GDAL_UNAVAILABLE` y el temporal queda vacío.
Notas: GDAL 3.12.2 se instaló después de esta tarea; el endpoint convierte un KML sintético a GPKG verificable. Falta migrar estilos QML e interfaz React.
