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
Decisión: excepción única y explícita: `MessageViewer` importa el componente público `AttachmentList`. No importa su `lib` ni estado interno.
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

## ADR-08 CSS global con tokens

Fecha: 2026-10-05. Estado: vigente.
Contexto: los estilos anteriores mezclaban colores y tamaños sueltos; no había escalas.
Decisión: una hoja `global.css` organizada en secciones numeradas, con tokens para color, tipografía, espaciado, radios, sombras, alturas de control y dimensiones de layout. Tailwind se mantiene por su preflight; no se usan utilidades en JSX.
Consecuencias: un estilo nuevo usa tokens existentes o crea uno documentado en `SISTEMA_VISUAL.md`.
