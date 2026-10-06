# Sistema visual

Base: Fluent 2, sistema de diseño público de Microsoft (repositorio `microsoft/fluentui`, licencia MIT), el mismo que usa Outlook. Valores reales en `src/app/styles/tokens.css`; este documento explica su uso. Si difieren, corregir en el mismo cambio.

## Principios

- Parecer el nuevo Outlook: cabecera azul con buscador, barra de apps, barra de comandos, bandeja y panel de lectura como paneles blancos redondeados sobre gris claro.
- El contenido del correo es protagonista; el cromo de la app es neutro.
- Color con significado: azul de marca para acción y selección, verde para privacidad o éxito, naranja para advertencia, rojo sólo para error.
- Sin logotipos ni nombre de producto de Microsoft (E-20).

## Color

- Marca (rampa brandWeb): `--brand-80` #0f6cbd primario, cabecera, iconos activos; `--brand-70` hover y enlaces; `--brand-40` pulsado; `--brand-150` fila seleccionada; `--brand-160` fondos tenues (buscador, iconos de estado, insignias); `--brand-140` y `--brand-100` reservados.
- Texto: `--fg-1` #242424 principal; `--fg-2` #424242 secundario; `--fg-3` #616161 metadatos, fechas, ayudas. Todos AA sobre blanco y `--bg-4`.
- Fondos: `--bg-1` paneles; `--bg-1-hover` y `--bg-1-pressed` estados; `--bg-2` pie de tarjeta; `--bg-3` fondo de miniaturas; `--bg-4` lienzo de la app; `--bg-6` hover sobre lienzo.
- Bordes: `--stroke-1` controles; `--stroke-1-hover`; `--stroke-2` tarjetas y separadores; `--stroke-3` divisores sutiles en listas.
- Estados (MessageBar): `--warning-*` (#fff9f5, #fdcfb4, icono #bc4b09), `--danger-*` (#fdf6f6, #f1bbbc, #bc2f32), `--success-*`, `--info-*`. El texto del mensaje va en `--fg-1`; sólo el icono lleva el color.
- Tipos de adjunto: `--kind-<tipo>` icono y `--kind-<tipo>-bg` tinte, de la paleta compartida de Fluent (PDF carmesí, Word azul, Excel verde, PowerPoint calabaza, imagen púrpura, CAD verde azulado, comprimido latón, texto ancla, multimedia magenta).
- Avatares: 10 tonos de la paleta de personas de Fluent (fondo tint40, texto shade30), asignados por hash estable del nombre.
- Visor: `--viewer-backdrop` #1f1f1f opaco, `--viewer-fg`, `--viewer-fg-muted`, `--viewer-control` y `--viewer-control-hover` translúcidos.

## Tipografía

- Familia: `--font-base` Segoe UI (Fluent). Lectura del cuerpo: `--font-reading` Aptos o Calibri. Código y texto plano de adjuntos: `--font-mono` Consolas.
- Rampa Fluent (tamaño/interlineado): 100 10/14 etiquetas de barra de apps y chips; 200 12/16 metadatos, fechas, destinatarios, adjuntos; 300 14/20 base, botones, filas; 400 16/22 títulos de panel; 500 20/28 asunto; 600 24/32 título de página; 700 28/36 portada. Cuerpo del correo: 15 px, interlineado 1.5.
- Pesos: 400 texto, 600 nombres, botones y títulos, 700 sólo números de pasos.

## Espaciado

- Escala Fluent: `--space-xxs` 2, `xs` 4, `s-nudge` 6, `s` 8, `m-nudge` 10, `m` 12, `l` 16, `xl` 20, `xxl` 24, `xxxl` 32; extensión `--space-huge` 48.
- `--pane-gap` 8 px entre paneles (0 en móvil).

## Forma, profundidad y movimiento

- Radios Fluent: `--radius-sm` 2, `md` 4 (botones, adjuntos, alertas), `lg` 6, `xl` 8 (paneles y tarjeta del mensaje), `circular`.
- Sombras Fluent (ambiente + clave): `--shadow-2` paneles, `--shadow-4` tarjeta del mensaje y hover de adjuntos, `--shadow-8` reservado, `--shadow-28` elementos flotantes.
- Movimiento: `--duration-faster` 100 ms, `--duration-normal` 200 ms, `--curve-easy-ease`.

## Dimensiones de layout e intrínsecas

- `--header-h` 48; `--appbar-w` 68 (botones de 56); `--list-w` 360 (320 bajo 1180, 400 desde 1600); `--reading-max` 1040 (1120 desde 1600).
- Controles Fluent: `--control-sm` 24, `--control-md` 32, `--control-lg` 40; con puntero táctil 32 y 40.
- Barra de comandos: alto mínimo 44.
- Avatares 32 (bandeja) y 40 (lector). Puntos de estado 32.
- Iconos de tipo: 24 (sm), 32 (md), 64 (lg).
- Tarjeta de miniatura: mínimo 176 de ancho, proporción 16:10. Chip de archivo: mínimo 240.
- Anchos máximos: EmptyState 520, portada y Ayuda 760, overlay de arrastre 360, panel de detalles del visor 320, hoja de texto del visor 960.
- Indicadores: barra de selección 3; chip 18 de alto; contador 20.

## Breakpoints

- 1600 o más: bandeja y lectura más anchas.
- 1180 o menos: bandeja 320; cabecera compacta.
- 960 o menos: el panel de detalles del visor flota sobre la imagen.
- 860 o menos: maestro-detalle; barra de apps abajo; paneles a sangre sin radio ni sombra.
- 640 o menos: nombre de la app e insignia sólo como icono; etiquetas del visor ocultas; miniaturas en 2 columnas; correo del remitente en línea propia.

## Componentes

- Button: `primary` (una por zona), `secondary`, `subtle` (barras de comandos y acciones terciarias), `danger`; tamaños `md` 32 y `sm` 24; `iconOnly` exige `aria-label`.
- SearchBox: 32 de alto, fondo `--brand-160` que pasa a blanco al enfocar, icono de lupa y botón borrar.
- Avatar: iniciales o icono de persona; decorativo.
- StatusAlert: MessageBar de Fluent; icono relleno de color, título en negrita en la misma línea.
- EmptyState: icono en círculo, título 20/28, texto y acciones; sin tarjeta propia (vive dentro de un panel).
- Spinner: anillo con arco de marca; versión `inverted` para el visor.
- Chip: 18 de alto, borde interior del color del estado.
- Skeleton: bloques `--skeleton` con brillo; reproduce la anatomía real.
- Tabs: TabList de Fluent; texto 14/20, seleccionada en semibold con indicador de marca de 3 px; hover con indicador gris.
- Imagen incrustada: tamaño natural hasta el ancho del cuerpo, borde `--stroke-3`, radio 4, cursor lupa; hover con `--shadow-4`.
- Mensaje citado: borde superior `--stroke-2`; avatar de 32, nombre semibold, correo y campos 12/16 en `--fg-3`, fecha a la derecha (debajo en móvil).
- Párrafos del cuerpo: separación `--space-s` en lugar de una línea en blanco.

## Iconografía

- `@fluentui/react-icons` (MIT), variantes `Regular` y `Filled` para el elemento activo. Tamaños por nombre (16, 20, 24); reescalar con CSS sólo dentro de `.file-icon`.
- Iconos decorativos con `aria-hidden`. Un icono sin texto visible necesita nombre accesible.

## Texto de interfaz

- Español neutro, tuteo, frases cortas. Vocabulario de Outlook en español: "datos adjuntos", "Bandeja", "Correo", "Para", "CC", "CCO".
- Botones con verbo: "Abrir MSG", "Limpiar bandeja", "Descargar", "Mostrar los 12".
- Datos ausentes: "Remitente desconocido", "Asunto no recuperado"; nunca placeholders genéricos.
