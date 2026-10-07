# Decisiones de arquitectura y diseño

Formato: contexto, decisión, consecuencias. Una decisión sólo se reemplaza con un ADR nuevo que la cite.

## ADR-01 Layout de cliente de correo a alto fijo

Fecha: 2026-10-05. Estado: vigente.
Contexto: la versión anterior crecía con el contenido; la bandeja se estiraba, aparecía scroll horizontal y la pantalla se veía vacía y desordenada.
Decisión: shell de `100dvh` con tres columnas (rail, bandeja, lector) y scroll independiente por panel. Lectura en tarjeta centrada con ancho máximo.
Consecuencias: aspecto estable en cualquier monitor. Todo contenido nuevo debe vivir dentro de un panel con scroll propio.

## ADR-02 Panel de lectura único en lugar de pestañas

Fecha: 2026-10-05. Estado: vigente. Reemplaza las pestañas Resumen/Cuerpo/Adjuntos.
Contexto: el usuario espera ver el correo como en Outlook; las pestañas escondían adjuntos y cuerpo, y "Resumen" no aportaba.
Decisión: una sola vista con encabezado, adjuntos y cuerpo, siguiendo el patrón de los lectores de correo sin copiar marca ni assets.
Consecuencias: los E2E ya no usan `role=tab`. Listas largas de adjuntos y destinatarios se pliegan para no empujar el cuerpo.

## ADR-03 Maestro-detalle en pantallas angostas

Fecha: 2026-10-05. Estado: vigente.
Contexto: bandeja y lector no caben juntos bajo 860 px; la tira horizontal anterior era incómoda.
Decisión: `data-pane` alterna bandeja y lector; rail como barra inferior; botón "‹ Bandeja (n)" en el lector.
Consecuencias: `App` mantiene el panel móvil; seleccionar muestra el lector.

## ADR-04 Descarga reenviando el MSG

Fecha: 2026-10-05. Estado: vigente.
Contexto: el backend no debe guardar correos ni adjuntos entre peticiones.
Decisión: para descargar, el navegador reenvía el `File` en memoria y el índice del adjunto.
Consecuencias: cada descarga vuelve a subir el MSG al servicio local; aceptable en loopback. No hay IDs de sesión.

## ADR-05 message-viewer compone attachments

Fecha: 2026-10-05. Estado: vigente.
Contexto: la regla general prohíbe que una feature importe detalles de otra.
Decisión: excepción única y explícita: `MessageViewer` importa la API pública de attachments (`AttachmentList`, `AttachmentViewer`, `useAttachmentFiles`). No importa su `lib` ni estado interno. Actualizada el 2026-10-06: el visor sube al lector para abrirse también desde las imágenes del cuerpo.
Consecuencias: si otra feature necesita adjuntos, extraer a componente compartido antes de duplicar.

## ADR-06 Arrastre a nivel de ventana

Fecha: 2026-10-05. Estado: vigente.
Contexto: soltar un archivo fuera de la zona hacía que el navegador lo abriera y se perdía la sesión en memoria.
Decisión: `useWindowFileDrop` escucha `dragenter/dragover/dragleave/drop` en `window`, previene la navegación y agrega los archivos. El overlay no intercepta eventos (`pointer-events: none`).
Consecuencias: la portada no tiene manejadores de drop propios; sólo refleja el estado `active`.

## ADR-07 Cuerpo en texto plano

Fecha: 2026-10-05. Estado: vigente.
Contexto: el HTML de un correo puede contener scripts, rastreadores y recursos remotos.
Decisión: el backend convierte HTML a texto y el frontend lo muestra en `<pre>` con fuente de lectura. Limpieza sólo de presentación (`tidyText`).
Consecuencias: se pierde formato visual (negritas, tablas). Cambiarlo exige sanitizador evaluado y un ADR nuevo.

## ADR-08 CSS por módulo con tokens

Fecha: 2026-10-05. Estado: vigente (actualizada el 2026-10-06).
Contexto: los estilos anteriores mezclaban valores sueltos; luego una sola hoja creció a casi 2000 líneas.
Decisión: tokens en `tokens.css` y un archivo CSS por módulo (máximo 250 líneas) importados en orden desde `global.css`. Tailwind se mantiene sólo por su preflight; sin utilidades en JSX.
Consecuencias: un estilo nuevo usa tokens existentes y vive en el archivo de su módulo (E-04, E-05).

## ADR-09 Fluent 2 como sistema de diseño

Fecha: 2026-10-06. Estado: vigente. Reemplaza la paleta propia anterior.
Contexto: el usuario pide que la interfaz se parezca lo más posible a Outlook.
Decisión: tokens públicos de Fluent 2 (`microsoft/fluentui`, MIT) para color, tipografía, espaciado, radios y sombras, e iconos `@fluentui/react-icons` (MIT). Se retira `lucide-react`. Layout del nuevo Outlook: cabecera de marca con buscador, barra de apps, barra de comandos y paneles blancos redondeados.
Consecuencias: aspecto familiar; sin logotipo, nombre de producto ni capturas de Microsoft (E-20). El paquete de iconos es grande en disco pero se importa por nombre y el bundle sólo incluye los usados.

## ADR-10 Miniaturas en la respuesta y vista previa bajo demanda

Fecha: 2026-10-06. Estado: vigente.
Contexto: los adjuntos sólo mostraban un icono; el usuario quiere ver imágenes y planos de frente.
Decisión: el backend incluye una miniatura JPEG por adjunto (`preview`, `preview_source`) y el visor pide el binario original, o `preview=true` para formatos que el navegador no muestra. `lib/api.ts` sólo acepta data URIs raster en base64.
Consecuencias: el JSON del análisis crece (con presupuesto en backend); se evita una petición por miniatura.

## ADR-11 Visor con diálogo nativo y visores del navegador

Fecha: 2026-10-06. Estado: vigente.
Contexto: mostrar PDF, texto y multimedia sin dependencias de render ni riesgo de HTML activo.
Decisión: `<dialog>` modal nativo; PDF en `<iframe>` con URL `blob:` y tipo `application/pdf`; texto en `<pre>`; vídeo y audio con elementos nativos; DWG/DXF/Office con su miniatura incrustada.
Consecuencias: el PDF lo dibuja el visor aislado del navegador; no hay zoom propio de imágenes (pendiente).

## ADR-12 Búsqueda local en la bandeja

Fecha: 2026-10-06. Estado: vigente.
Contexto: con muchos MSG abiertos hace falta encontrarlos como en Outlook.
Decisión: buscador en la cabecera que filtra en memoria con `filterQueue` (sin tildes ni mayúsculas, todas las palabras).
Consecuencias: sin índices ni almacenamiento; el costo es lineal y suficiente para una sesión local.

## ADR-13 Imágenes en su posición y pestaña de adjuntos

Fecha: 2026-10-06. Estado: vigente.
Contexto: las imágenes incrustadas aparecían sólo en un apartado, sin el orden del correo.
Decisión: el cuerpo coloca cada `[cid:…]` como miniatura del adjunto (Content-ID o nombre). Cuando eso ocurre, el lector muestra pestañas: Mensaje (adjuntos no incrustados y cuerpo) y Datos adjuntos (galería completa como antes). Sin imágenes en posición no hay pestañas.
Consecuencias: la lectura se parece a Outlook sin perder la galería; no se renderiza HTML.

## ADR-14 Historial citado estructurado

Fecha: 2026-10-06. Estado: vigente.
Contexto: las respuestas traen el hilo completo como texto, difícil de seguir.
Decisión: `splitThread` detecta bloques De/Enviado/Para/CC/Asunto (español e inglés, con separadores de Outlook) y `QuotedThread` los muestra plegados, con avatar, nombre y fecha por mensaje. Se limpian los `<mailto:…>` duplicados.
Consecuencias: un bloque que no llega a "Asunto" en 10 líneas no se trata como cita, para evitar falsos positivos con "De:" dentro del texto.

## ADR-15 Asunto deducido sólo si se verifica

Fecha: 2026-10-06. Estado: vigente.
Contexto: si el MSG pierde el asunto, el nombre del archivo es una pista pero con caracteres sustituidos (`:` y `|` pasan a `_`).
Decisión: se toma el asunto del primer mensaje citado y sus variantes con RE/RV/FW; sólo se acepta si, saneado como lo hace Outlook, reproduce exactamente el nombre del archivo. Se avisa "Asunto deducido…".
Consecuencias: nunca se inventa un asunto; si no coincide, se muestra el nombre del archivo con su aviso.

## ADR-16 Búsqueda con resaltado como en Outlook

Fecha: 2026-10-06. Estado: vigente.
Contexto: el buscador ya filtraba entre todos los correos, pero no mostraba dónde coincidía, y las coincidencias del historial plegado no se veían.
Decisión: `findRanges` normaliza carácter a carácter guardando la posición original, así el resaltado sin tildes cae en su sitio. La bandeja muestra el fragmento de la coincidencia; el lector resalta con `<mark>`, cuenta coincidencias y despliega el historial si hace falta. Los términos llegan al lector por contexto (`HighlightContext`) para no atravesar cinco niveles de props. Atajo `/`.
Consecuencias: sin índices ni almacenamiento; costo lineal por correo, suficiente para una sesión local.

## ADR-17 Imágenes reconstruidas y no recuperadas

Fecha: 2026-10-06. Estado: vigente.
Contexto: en MSG dañados el backend puede reconstruir la posición de algunas imágenes por sus medidas (ADR-B11) y otras no.
Decisión: una imagen con `content_id_inferred` se muestra en su lugar con la nota "Ubicación reconstruida" (explicación en el tooltip). Un `cid` sin adjunto se muestra como un aviso compacto "Imagen no recuperada · nombre" en lugar de un hueco grande.
Consecuencias: el usuario ve el orden del correo sin confundir inferencias con datos leídos.

## ADR-18 Correos adjuntos navegables en el lector

Fecha: 2026-10-06. Estado: vigente.
Contexto: el backend entrega cada correo adjunto ya leído dentro de `Attachment.message` (ADR-B13). Outlook lo abre en otra ventana; aquí no hay ventanas.
Decisión: `MessageReader` guarda la ruta de posiciones abiertas y muestra el correo de esa ruta con `MessageViewer key={ruta}`, que reinicia pestañas, visor y caché de adjuntos. Una barra "Correo adjunto" con "Volver" sube un nivel. Al navegar, el contenedor que se desplaza vuelve al inicio y el foco pasa al asunto. Las descargas internas mandan `message_path`.
Consecuencias: abrir un correo adjunto no hace peticiones; cada descarga interna reenvía el MSG y el backend recopia cada nivel. App no conoce la ruta: elegir otro correo de la bandeja vuelve al principal.

## ADR-19 Enlaces de adjuntos sólo http y https

Fecha: 2026-10-06. Estado: vigente.
Contexto: un adjunto de OneDrive, SharePoint o una carpeta de red sólo trae su dirección, que es texto del correo y podría ser cualquier esquema.
Decisión: `isWebLink` acepta sólo `http://` y `https://`; esa dirección se ofrece como "Abrir enlace" en otra pestaña con `noopener noreferrer`. Cualquier otra se muestra como texto seleccionable. Sin descarga ni miniatura.
Consecuencias: la aplicación nunca pide la dirección (RQ-01); el usuario la abre con su navegador y su cuenta. Las rutas de red se copian a mano porque el navegador bloquea `file:` desde una página web.

## ADR-20 Enlaces en el cuerpo de texto

Fecha: 2026-10-06. Estado: vigente. Mantiene ADR-07 y aplica ADR-19.
Contexto: el cuerpo es texto plano; el texto de Outlook y el HTML convertido (PEN-08) traen las direcciones como `texto <url>`, pero no se podían abrir.
Decisión: `splitLinks` separa las direcciones `http`/`https` del texto sin alterar ningún carácter y `LinkedText` las muestra como `<a>` con esa misma dirección como contenido, en otra pestaña y con `noopener noreferrer`. No se interpreta HTML: un destino distinto del texto visible es imposible.
Consecuencias: el usuario ve adónde lleva cada enlace antes de abrirlo. Un término de búsqueda que cruza el borde de un enlace no se resalta entero.
