# Requerimientos y cobertura

## Prioridad de uso

Pensada para una persona que no conoce MSG, OLE, FAT ni metadata. Debe poder abrir un correo, leer asunto, remitente, destinatarios, fecha y texto, ver de frente imágenes, PDF y planos, y descargar cualquier adjunto. El diagnóstico técnico queda fuera de la vista principal; las propiedades de cada adjunto se consultan en el panel Detalles del visor.

## Requisitos verificables

- RQ-01 Local: loopback, sin cuenta, base de datos, nube, telemetría ni historial.
- RQ-02 Privacidad: estado en memoria del navegador; temporales efímeros del backend borrados al terminar.
- RQ-03 Original intacto: sólo se trabaja sobre copias temporales; la reparación de FAT ocurre en una copia.
- RQ-04 Correo legible: asunto, remitente, destinatarios Para/CC/CCO, fechas y cuerpo de texto. Si el parser o las propiedades cortas fallan, se identifican desde propiedades MAPI alternativas o los encabezados de transporte.
- RQ-05 Adjuntos de cualquier tipo: todo adjunto con stream legible se lista y se descarga con sus bytes exactos, sea imagen, PDF, Office, AutoCAD, comprimido, multimedia u otro.
- RQ-06 Vista previa: imágenes (PNG, JPEG, GIF, BMP, TIFF, WEBP, ICO; EMF/WMF en Windows) con miniatura; PDF, texto, vídeo y audio se muestran en el navegador; TIFF/EMF se convierten a JPEG bajo demanda.
- RQ-07 AutoCAD: DWG desde R13 y DXF ASCII muestran la miniatura que AutoCAD guardó dentro (PNG o BMP), además de versión de formato (DWG) o versión, unidades y capas (DXF).
- RQ-08 Office: DOCX, XLSX y PPTX muestran la portada `docProps/thumbnail` cuando el archivo la incluye, y sus propiedades de documento.
- RQ-09 Sin límite fijo de peso: MSG y adjuntos se procesan por bloques; el plazo crece con el tamaño.
- RQ-10 Lectura parcial: lo legible se conserva; PNG/PDF completos fuera de enlaces OLE se ofrecen como recuperados.
- RQ-11 Seguridad: sin macros ni HTML activo; Pillow con lista cerrada de formatos; Host y Origin externos rechazados.
- RQ-12 Pruebas: MSG y adjuntos sintéticos; nunca correos privados en el repositorio.
- RQ-13 Imágenes en posición: las imágenes incrustadas se marcan en el cuerpo (`[cid:…]`) y se enlazan con su adjunto por Content-ID o nombre. En un MSG dañado se recupera el HTML del RTF suelto y la posición se reconstruye sólo con evidencia inequívoca de medidas; lo ambiguo se queda en la lista de adjuntos y la interfaz lo dice.

## Límites honestos

- No se recuperan datos que ya no están en el archivo.
- La miniatura de un DWG/DXF/Office es la que guardó el programa al último guardado; puede no coincidir con el contenido actual y no existe si se desactivó al guardar.
- No hay render de DWG ni de páginas PDF en el backend; el PDF lo dibuja el visor del navegador.
- EMF/WMF sólo se convierten donde Pillow puede renderizarlos (Windows).
- Un corte de energía o terminación forzada puede impedir la limpieza de temporales.

## Pendientes por revisar (backlog priorizado)

Cada pendiente se cita por su ID. Al tomar uno: crear o actualizar la spec correspondiente con sus criterios de aceptación y mover aquí su estado. Prioridad según frecuencia en correo corporativo y valor para el usuario.

### PEN-01 Correos adjuntos dentro del correo

Prioridad: alta. Alcance: backend y frontend. Estado: pendiente.
Situación: un MSG o EML reenviado "como adjunto" aparece como "Adjunto MSG anidado u objeto embebido: no se expande"; no se puede leer.
Hacer: analizar el mensaje interno con el mismo flujo (límite de profundidad y de tiempo) y mostrarlo en el lector como un correo propio, con navegación de vuelta al correo contenedor.
Terminado cuando: un MSG sintético con otro MSG adjunto muestra remitente, asunto, texto y adjuntos descargables del interno; prueba de profundidad máxima.

### PEN-02 Adjuntos en la nube o por referencia

Prioridad: alta. Alcance: backend y frontend. Estado: pendiente.
Situación: los adjuntos de OneDrive/SharePoint o por referencia (método de adjunto distinto de "por valor") no traen bytes y hoy se informan, por error, como adjunto anidado.
Hacer: leer el método de adjunto (`0x3705`) y la ruta o URL (`0x370D`, propiedades de adjunto web) y mostrarlos como enlace, avisando que el archivo no viaja dentro del correo.
Terminado cuando: un adjunto por referencia sintético se muestra como enlace con su nombre y no ofrece una descarga vacía.

### PEN-03 Rescate de datos sueltos ampliado

Prioridad: alta. Alcance: backend. Estado: pendiente.
Situación: el rescate fuera de los enlaces OLE sólo reconoce PNG, PDF y el RTF del cuerpo; las imágenes sólo se rescatan si hubo reparación de FAT; un archivo que perdió la firma OLE inicial se rechaza entero.
Hacer: validar y rescatar JPEG (SOI/EOI y decodificación de prueba), GIF y ZIP/Office (directorio central); intentar el rescate también sin reparación de FAT cuando el parser falla; ante firma OLE ausente, ofrecer lectura de rescate en lugar de rechazo.
Terminado cuando: pruebas sintéticas con cada formato desconectado y con la cabecera OLE borrada recuperan los archivos sin duplicar adjuntos ya legibles.

### PEN-04 Mini stream fragmentado

Prioridad: media. Alcance: backend. Estado: investigado.
Situación: en el MSG real del usuario el mini stream no es contiguo; se pierden nombres, Content-ID y destinatarios cortos. Suponer contigüidad dio datos falsos y se descartó.
Hacer: reconstruir la cadena del mini stream con los tramos válidos de la FAT y validar cada propiedad recuperada contra fuentes independientes (encabezados de transporte, tamaños declarados).
Terminado cuando: el asunto recuperado del mini stream coincide con el `Subject` de los encabezados en un caso sintético fragmentado.

### PEN-05 Vistas previas que faltan

Prioridad: media. Alcance: backend y frontend. Estado: pendiente.
Situación: sin miniatura para fotos HEIC de iPhone, Office antiguo (.doc, .xls, .ppt), primera página de PDF; los ZIP no muestran su contenido.
Hacer: evaluar `pillow-heif` (licencia y tamaño); leer la miniatura de `SummaryInformation` de Office antiguo; evaluar un motor de render de PDF con licencia compatible; listar entradas de ZIP con los mismos límites anti bomba.
Terminado cuando: cada formato tiene miniatura o listado en una prueba sintética y la dependencia nueva está justificada en STACK.

### PEN-06 Correos cifrados, firmados o con permisos

Prioridad: media. Alcance: backend y frontend. Estado: pendiente.
Situación: S/MIME (`smime.p7m`) y contenido con permisos (IRM, `.rpmsg`) no se detectan; el usuario ve un correo vacío o un adjunto raro.
Hacer: detectar la clase y el tipo; en firmados (no cifrados) extraer el contenido interno; en cifrados, avisar con claridad que no se puede leer sin la clave.
Terminado cuando: casos sintéticos firmado y cifrado muestran contenido o aviso correcto.

### PEN-07 Invitaciones, contactos y tareas

Prioridad: media. Alcance: backend y frontend. Estado: pendiente.
Situación: los MSG de calendario (`IPM.Schedule.Meeting*`, `IPM.Appointment`), contactos y tareas se muestran como correo genérico; los `.ics` adjuntos sólo se descargan.
Hacer: mostrar fecha, hora, lugar y asistentes de una invitación; ficha básica de contacto; vista de texto de `.ics`.
Terminado cuando: un MSG de reunión sintético muestra sus datos de agenda.

### PEN-08 Cuerpo con formato y enlaces

Prioridad: baja (requiere decisión). Alcance: backend y frontend. Estado: pendiente.
Situación: por seguridad el cuerpo se muestra como texto (ADR-07): se pierden tablas, negritas y la dirección real de los enlaces.
Hacer: como paso inmediato, conservar la URL de cada enlace en el texto (`texto <url>`). Como paso mayor, evaluar HTML saneado en un iframe aislado sin recursos remotos; exige un ADR que reemplace ADR-07.
Terminado cuando: los enlaces del HTML conservan su destino visible y, si se aprueba el ADR, el HTML se muestra sin ejecutar scripts ni cargar nada externo.

### PEN-09 Objetos OLE embebidos

Prioridad: baja. Alcance: backend. Estado: pendiente.
Situación: objetos incrustados (método de adjunto 6, por ejemplo una hoja de Excel pegada en un RTF) no se expanden.
Hacer: extraer el stream del objeto y tratarlo como adjunto cuando su formato sea reconocible.

### PEN-10 Corpus real y pruebas en Linux

Prioridad: media (calidad). Alcance: proyecto. Estado: pendiente.
Situación: sólo se probó con un MSG dañado real; la suite no se ejecutó en Linux en las últimas sesiones.
Hacer: reunir un corpus autorizado de corrupciones reales sin correos privados versionados y ejecutar backend y E2E en Linux.

### PEN-11 Otros

- Render completo de DWG con una herramienta evaluada y licenciada.
- Descargar todos los adjuntos en un ZIP.
- Empaquetado instalable para Windows.
- EMF/WMF sin miniatura fuera de Windows (límite de Pillow).
