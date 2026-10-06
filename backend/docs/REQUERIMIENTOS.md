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

## Pendientes fuera del alcance actual

- Adjuntos MSG anidados y objetos OLE embebidos.
- Render completo de DWG con una herramienta evaluada y licenciada.
- Miniatura de la primera página de PDF (requiere motor de render).
- Descargar todos los adjuntos en un ZIP.
- Corpus autorizado de corrupciones reales, sin correos privados.
- Empaquetado instalable para Windows.
