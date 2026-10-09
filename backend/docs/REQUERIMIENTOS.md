# Requerimientos y cobertura

## Prioridad de uso

Pensada para una persona que no conoce MSG, OLE, FAT ni metadata. Debe poder abrir un correo, leer asunto, remitente, destinatarios, fecha y texto, ver de frente imágenes, PDF y planos, y descargar cualquier adjunto. El diagnóstico técnico queda fuera de la vista principal; las propiedades de cada adjunto se consultan en el panel Detalles del visor.

## Requisitos verificables

- RQ-01 Local: loopback por defecto; acceso desde la red local sólo si se configura de forma explícita (ADR-B12). Sin cuenta, base de datos, nube, telemetría ni historial.
- RQ-02 Privacidad: estado en memoria del navegador; temporales efímeros del backend borrados al terminar.
- RQ-03 Original intacto: sólo se trabaja sobre copias temporales; la reparación de cabecera (firma, FAT y MiniFAT) ocurre en una copia.
- RQ-04 Correo legible: asunto, remitente, destinatarios Para/CC/CCO, fechas y cuerpo de texto. Si el parser o las propiedades cortas fallan, se identifican desde propiedades MAPI alternativas o los encabezados de transporte.
- RQ-05 Adjuntos de cualquier tipo: todo adjunto con stream legible se lista y se descarga con sus bytes exactos, sea imagen, PDF, Office, AutoCAD, comprimido, multimedia u otro. Un correo adjunto se lee como un correo propio y se descarga como `.msg`. Un adjunto en la nube o en una ruta se muestra como enlace: sus bytes no viajan en el correo.
- RQ-06 Vista previa: imágenes (PNG, JPEG, GIF, BMP, TIFF, WEBP, ICO; EMF/WMF en Windows) con miniatura; PDF, texto, vídeo y audio se muestran en el navegador; TIFF/EMF se convierten a JPEG bajo demanda.
- RQ-07 AutoCAD: DWG desde R13 y DXF ASCII muestran la miniatura que AutoCAD guardó dentro (PNG o BMP), además de versión de formato (DWG) o versión, unidades y capas (DXF).
- RQ-08 Office: DOCX, XLSX y PPTX muestran la portada `docProps/thumbnail` cuando el archivo la incluye, y sus propiedades de documento.
- RQ-09 Sin límite fijo de peso: MSG y adjuntos se procesan por bloques; el plazo crece con el tamaño.
- RQ-10 Lectura parcial: lo legible se conserva; PNG, JPEG, GIF, PDF y ZIP/Office completos fuera de los streams legibles se ofrecen como recuperados cuando hay daño; un MSG sin firma o sin cabecera se lee con lo que sigue entero.
- RQ-11 Seguridad: sin macros ni HTML activo; Pillow con lista cerrada de formatos; Host y Origin fuera de la lista permitida rechazados.
- RQ-12 Pruebas: MSG y adjuntos sintéticos; nunca correos privados en el repositorio.
- RQ-15 Correos S/MIME: un correo firmado en claro muestra su texto y sus adjuntos y dice que la firma no se comprueba; uno opaco o cifrado lo explica y permite descargar el `smime.p7m`.
- RQ-14 Otros elementos de Outlook: una reunión, cita, contacto o tarea muestra sus datos (cuándo, dónde, quiénes, teléfonos, estado) sobre el texto; los `.ics` y `.vcf` adjuntos se ven como texto.
- RQ-13 Imágenes en posición: las imágenes incrustadas se marcan en el cuerpo (`[cid:…]`) y se enlazan con su adjunto por Content-ID o nombre. En un MSG dañado se recupera el HTML del RTF suelto y la posición se reconstruye sólo con evidencia inequívoca de medidas; lo ambiguo se queda en la lista de adjuntos y la interfaz lo dice.

## Límites honestos

- No se recuperan datos que ya no están en el archivo.
- La miniatura de un DWG/DXF/Office es la que guardó el programa al último guardado; puede no coincidir con el contenido actual y no existe si se desactivó al guardar.
- No hay render de DWG ni de páginas PDF en el backend; el PDF lo dibuja el visor del navegador.
- EMF/WMF sólo se convierten donde Pillow puede renderizarlos (Windows).
- Un corte de energía o terminación forzada puede impedir la limpieza de temporales.
- La firma S/MIME no se verifica, un correo firmado en formato opaco no se desempaqueta y uno cifrado no se lee.
- Sin cabecera legible sólo se rescata lo que sigue contiguo y se valida: no hay propiedades MAPI, adjuntos fragmentados ni nombres originales de adjuntos.

## Pendientes por revisar (backlog priorizado)

Cada pendiente se cita por su ID. Al tomar uno: crear o actualizar la spec correspondiente con sus criterios de aceptación y mover aquí su estado. Prioridad según frecuencia en correo corporativo y valor para el usuario.

Estado del proyecto: cerrado momentáneamente el 2026-10-08 por decisión del usuario. El alcance principal está cumplido y en uso; lo abierto queda como backlog para retomar y no bloquea el uso diario. Orden recomendado al retomar: PEN-10 (E2E en Linux), PEN-14, PEN-05, PEN-09; PEN-08 y el corpus de PEN-10 esperan una decisión o material del usuario.

Resumen al 2026-10-08:
- Terminadas: PEN-01, PEN-02, PEN-03, PEN-04, PEN-06, PEN-07, PEN-12, PEN-13.
- Parciales: PEN-08 (falta decidir HTML saneado), PEN-10 (backend probado en Linux; faltan E2E en Linux y corpus), PEN-11 (ZIP hecho; faltan DWG, instalador y EMF fuera de Windows).
- Por hacer, en orden: PEN-05, PEN-14, PEN-09.

### PEN-01 Correos adjuntos dentro del correo

Prioridad: alta. Alcance: backend y frontend. Estado: terminada (2026-10-06).
Hecho: correo adjunto (método 5) leído con el mismo flujo, hasta 3 niveles y 20 correos por análisis; navegación con "Volver"; descargas internas con `message_path`; descarga del correo adjunto como `.msg` (ADR-B13, ADR-18).
Hecho también: `.eml` adjunto (biblioteca estándar) y `.msg` adjunto como archivo, con sus correos internos y descargas (ADR-B15).
Situación original: un MSG o EML reenviado "como adjunto" aparece como "Adjunto MSG anidado u objeto embebido: no se expande"; no se puede leer.
Hacer: analizar el mensaje interno con el mismo flujo (límite de profundidad y de tiempo) y mostrarlo en el lector como un correo propio, con navegación de vuelta al correo contenedor.
Terminado cuando: un MSG sintético con otro MSG adjunto muestra remitente, asunto, texto y adjuntos descargables del interno; prueba de profundidad máxima.

### PEN-02 Adjuntos en la nube o por referencia

Prioridad: alta. Alcance: backend y frontend. Estado: terminada (2026-10-06).
Hecho: método de adjunto y dirección (`0x3705`, `0x370D`, `0x3708`) leídos; `kind=link` con su dirección; la interfaz muestra dónde vive, sin descarga, y abre sólo http y https en otra pestaña (ADR-B14, ADR-19).
Situación original: los adjuntos de OneDrive/SharePoint o por referencia (método de adjunto distinto de "por valor") no traen bytes y hoy se informan, por error, como adjunto anidado.
Hacer: leer el método de adjunto (`0x3705`) y la ruta o URL (`0x370D`, propiedades de adjunto web) y mostrarlos como enlace, avisando que el archivo no viaja dentro del correo.
Terminado cuando: un adjunto por referencia sintético se muestra como enlace con su nombre y no ofrece una descarga vacía.

### PEN-03 Rescate de datos sueltos ampliado

Prioridad: alta. Alcance: backend. Estado: terminada (2026-10-06).
Hecho: JPEG, GIF y ZIP/Office validados; exclusión por sectores y mini sectores alcanzables, por anidamiento y por duplicado; activación también con el parser caído (con la descarga coherente); firma repuesta en copia y lectura de rescate sin cabecera (ADR-B16).
Situación original: el rescate fuera de los enlaces OLE sólo reconoce PNG, PDF y el RTF del cuerpo; las imágenes sólo se rescatan si hubo reparación de FAT; un archivo que perdió la firma OLE inicial se rechaza entero.
Hacer: validar y rescatar JPEG (SOI/EOI y decodificación de prueba), GIF y ZIP/Office (directorio central); intentar el rescate también sin reparación de FAT cuando el parser falla; ante firma OLE ausente, ofrecer lectura de rescate en lugar de rechazo.
Terminado cuando: pruebas sintéticas con cada formato desconectado y con la cabecera OLE borrada recuperan los archivos sin duplicar adjuntos ya legibles.

### PEN-04 Mini stream fragmentado

Prioridad: media. Alcance: backend. Estado: terminada (2026-10-08).
Hecho: la causa real era la ubicación de la MiniFAT borrada de la cabecera; la MiniFAT seguía entera como cadena de la FAT. Se ubica la única tabla que explica cada stream pequeño y se repone en la copia (ADR-B19). En el MSG real: 254 de 254 cadenas válidas, asunto y remitente idénticos a los encabezados, parser abierto, nombres y Content-ID reales en los 2 adjuntos del directorio y los mismos 12 adjuntos descargables.
Situación original: en el MSG real del usuario el mini stream no es contiguo; se pierden nombres, Content-ID y destinatarios cortos. Suponer contigüidad dio datos falsos y se descartó.
Hacer: reconstruir la cadena del mini stream con los tramos válidos de la FAT y validar cada propiedad recuperada contra fuentes independientes (encabezados de transporte, tamaños declarados).
Terminado cuando: el asunto recuperado del mini stream coincide con el `Subject` de los encabezados en un caso sintético fragmentado.

### PEN-05 Vistas previas que faltan

Prioridad: media. Alcance: backend y frontend. Estado: pendiente.
Situación: sin miniatura para fotos HEIC de iPhone, Office antiguo (.doc, .xls, .ppt), primera página de PDF; los ZIP no muestran su contenido.
Hacer: evaluar `pillow-heif` (licencia y tamaño); leer la miniatura de `SummaryInformation` de Office antiguo; evaluar un motor de render de PDF con licencia compatible; listar entradas de ZIP con los mismos límites anti bomba.
Terminado cuando: cada formato tiene miniatura o listado en una prueba sintética y la dependencia nueva está justificada en STACK.

### PEN-06 Correos cifrados, firmados o con permisos

Prioridad: media. Alcance: backend y frontend. Estado: terminada (2026-10-07).
Hecho: firmado en claro con su contenido y adjuntos (análisis y descarga); opaco y cifrado detectados por OID, sin cuerpo inventado; permisos IRM detectados; avisos en el lector (ADR-B18, ADR-22).
Situación original: S/MIME (`smime.p7m`) y contenido con permisos (IRM, `.rpmsg`) no se detectan; el usuario ve un correo vacío o un adjunto raro.
Hacer: detectar la clase y el tipo; en firmados (no cifrados) extraer el contenido interno; en cifrados, avisar con claridad que no se puede leer sin la clave.
Terminado cuando: casos sintéticos firmado y cifrado muestran contenido o aviso correcto.

### PEN-07 Invitaciones, contactos y tareas

Prioridad: media. Alcance: backend y frontend. Estado: terminada (2026-10-07).
Hecho: `item` con reunión, cancelación, respuesta, cita, contacto o tarea; tarjeta en el lector; búsqueda en lugar y asistentes; `.ics`, `.vcs` y `.vcf` como texto en el visor (ADR-B17, ADR-21).
Situación original: los MSG de calendario (`IPM.Schedule.Meeting*`, `IPM.Appointment`), contactos y tareas se muestran como correo genérico; los `.ics` adjuntos sólo se descargan.
Hacer: mostrar fecha, hora, lugar y asistentes de una invitación; ficha básica de contacto; vista de texto de `.ics`.
Terminado cuando: un MSG de reunión sintético muestra sus datos de agenda.

### PEN-08 Cuerpo con formato y enlaces

Prioridad: baja (requiere decisión). Alcance: backend y frontend. Estado: parcial (paso inmediato terminado el 2026-10-06; HTML saneado pendiente de decisión).
Hecho: el HTML a texto conserva el destino real de cada enlace web (`texto <url>`) y el lector muestra las direcciones http/https del texto como enlaces que se abren en otra pestaña (ADR-20 del frontend).
Situación original: por seguridad el cuerpo se muestra como texto (ADR-07): se pierden tablas, negritas y la dirección real de los enlaces.
Hacer: como paso inmediato, conservar la URL de cada enlace en el texto (`texto <url>`). Como paso mayor, evaluar HTML saneado en un iframe aislado sin recursos remotos; exige un ADR que reemplace ADR-07.
Terminado cuando: los enlaces del HTML conservan su destino visible y, si se aprueba el ADR, el HTML se muestra sin ejecutar scripts ni cargar nada externo.

### PEN-09 Objetos OLE embebidos

Prioridad: baja. Alcance: backend. Estado: pendiente.
Situación: objetos incrustados (método de adjunto 6, por ejemplo una hoja de Excel pegada en un RTF) no se expanden.
Hacer: extraer el stream del objeto y tratarlo como adjunto cuando su formato sea reconocible.

### PEN-10 Corpus real y pruebas en Linux

Prioridad: media (calidad). Alcance: proyecto. Estado: parcial.
Hecho (2026-10-08): backend en Linux (contenedor `python:3.12-slim`, kernel WSL2): pytest, ruff check y ruff format aprobados (PLAN_CALIDAD, Comandos).
Falta: E2E del frontend en Linux (contenedor de Playwright) y el corpus autorizado, que depende del usuario.
Situación original: sólo se probó con un MSG dañado real; la suite no se ejecutó en Linux en las últimas sesiones.
Hacer: reunir un corpus autorizado de corrupciones reales sin correos privados versionados y ejecutar backend y E2E en Linux.

### PEN-12 Acceso LAN documentado

Prioridad: alta (coherencia). Alcance: proyecto. Estado: terminada (2026-10-06).
Situación: el commit `07a9b11` permitió abrir la app desde otra PC configurando Host y Origin por entorno, pero RQ-01, guías y stack seguían diciendo "sólo loopback" y no había ADR.
Hecho: ADR-B12 (modo LAN opcional, riesgos y límites), RQ-01, CA-08, guía, arquitectura, API y stack actualizados; `env_list` probado en `test_config.py`.

### PEN-13 Nombre de descarga entre orígenes

Prioridad: media. Alcance: backend. Estado: terminada (2026-10-07).
Situación: con Vite en desarrollo o en modo LAN (orígenes distintos) el navegador no expone `Content-Disposition`; un correo adjunto se guardaba sin `.msg` y un ZIP con nombre genérico.
Hecho: `expose_headers=["Content-Disposition"]` en CORS; el frontend arma además el nombre del ZIP desde el del MSG. Prueba: `test_archive.py::test_download_name_is_readable_from_another_origin`.

### PEN-14 Mejoras menores detectadas

Prioridad: baja. Alcance: frontend y proyecto. Estado: pendiente.
- Un correo cifrado u opaco dice "No se pudo recuperar el texto de este correo"; debería decir que el texto está cifrado o protegido.
- `MessageViewer.tsx` tiene 153 líneas (P-07 pide separar desde 150): extraer el conteo de coincidencias a un hook.
- Comparación automática con el MSG real del usuario (sólo local, sin versionarlo) para repetir la verificación de PEN-03 en cada cambio de rescate.

### PEN-11 Otros

Estado: parcial.

- Render completo de DWG con una herramienta evaluada y licenciada.
- Descargar todos los adjuntos en un ZIP: terminado el 2026-10-07 (`POST /attachments`, botón "Descargar todo").
- Empaquetado instalable para Windows.
- EMF/WMF sin miniatura fuera de Windows (límite de Pillow).
