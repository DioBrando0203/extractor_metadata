# Sistema visual

Fuente de verdad de los valores: `src/app/styles/global.css`, sección 1. Este documento explica cuándo usar cada token. Si difieren, corregir el que esté mal en el mismo cambio.

## Principios

- Parecer un cliente de correo profesional: denso pero respirable, jerarquía clara, cero decoración gratuita.
- Inspirado en el patrón de Outlook, sin su marca, logos, iconos propios ni nombre en la interfaz salvo en el titular de la portada.
- El contenido del correo es protagonista; el cromo de la app es neutro.
- Color con significado: azul acción y selección, verde confirmación y privacidad, ámbar advertencia, rojo sólo error.

## Color

- Marca: `--brand-900` barra superior; `--brand-600` botón primario, selección e iconos activos; `--brand-700` hover y texto activo; `--brand-800` pulsado; `--brand-50` fondo seleccionado; `--brand-100` borde hover.
- Texto: `--ink` principal; `--ink-soft` secundario fuerte (asunto en bandeja, destinatarios); `--muted` secundario (fechas, metadatos), AA garantizado; `--subtle` sólo bordes e iconos decorativos, nunca texto.
- Superficies: `--surface` tarjetas y paneles; `--surface-alt` rail y pie de tarjeta; `--surface-hover` hover de filas y botones ghost; `--canvas` fondo del lector.
- Líneas: `--line` separadores; `--line-strong` borde de botón secundario y zona de arrastre.
- Estados: `--good*`, `--warn*`, `--danger*`, `--info*` con sus `-bg` y `-line`.
- Tipos de adjunto: `--kind-<tipo>` icono y `--kind-<tipo>-bg` fondo.
- Avatares: `--avatar-N-fg` sobre `--avatar-N-bg`, seis tonos asignados por hash estable del nombre.
- Foco: `--focus`, contorno de 2 px con separación de 2 px.

## Tipografía

- UI: `--font-ui` (Segoe UI Variable/Segoe UI y equivalentes del sistema). Sin fuentes remotas.
- Lectura del cuerpo: `--font-reading` (Aptos, Calibri, luego UI).
- Escala: `--text-2xs` 11 px etiquetas mínimas; `--text-xs` 12 px metadatos; `--text-sm` 13 px texto secundario y botones; `--text-md` 14 px base; `--text-body` 15 px cuerpo y remitente; `--text-lg` 16 px títulos de sección; `--text-xl` 20 px asunto; `--text-2xl` 26 px título de página; `--text-display` 28 a 38 px sólo portada.
- Pesos: 400 texto, `--weight-medium` 500 asunto en bandeja, `--weight-semibold` 600 nombres y botones, `--weight-bold` 700 títulos de página.
- Interlineado: 1.45 base, 1.55 cuerpo del correo, 1.6 párrafos de ayuda.

## Espaciado

- Escala de 4 px: `--space-1` 4, `-2` 8, `-3` 12, `-4` 16, `-5` 20, `-6` 24, `-7` 28, `-8` 32, `-10` 40, `-14` 56.
- `--gutter`: margen lateral de la tarjeta de lectura. 28 px escritorio, 24 px bajo 1180, 16 px bajo 860.
- Valores de 1 a 6 px sólo para ajustes ópticos finos (gap de icono y texto, indicadores). Ver E-01.

## Forma, profundidad y movimiento

- Radios: `--radius-sm` 6 botones y chips; `--radius-md` 8 filas, adjuntos, alertas; `--radius-lg` 12 tarjetas; `--radius-pill` insignias.
- Sombras: `--shadow-1` tarjetas en reposo; `--shadow-2` elementos flotantes (overlay). No apilar sombras.
- Movimiento: `--duration` 120 ms con `--ease`. Animaciones continuas (spinner, esqueleto) sólo bajo `prefers-reduced-motion: no-preference`.

## Dimensiones de layout

- `--topbar-h` 48 px.
- `--rail-w` 72 px.
- `--list-w` 340 px; 300 px bajo 1180; 380 px desde 1600.
- `--reading-max` 960 px; 1040 px desde 1600.
- Controles: `--control-md` 34 px y `--control-sm` 28 px; 40 y 36 px con puntero táctil.
- Avatares y puntos de estado: 32 px en bandeja, 40 px en lector. Iconos de adjunto: 36 px.
- Anchos máximos intrínsecos: EmptyState 560 px, portada y Ayuda 760 px, overlay de arrastre 360 px.
- Indicadores: barra de selección y de rail 3 px; chip 18 px de alto; contador 20 px.

## Breakpoints

- 1600 px o más: bandeja y lectura más anchas.
- 1180 px o menos: bandeja 300 px y gutter 24 px.
- 860 px o menos: maestro-detalle, rail inferior, tarjeta de lectura a sangre.
- 520 px o menos: asunto 16 px, insignia sólo icono, correo del remitente en línea propia.

## Componentes

- Button: variantes `primary` (una por zona), `secondary`, `ghost` (acciones terciarias), `danger`; tamaños `md` y `sm`; `iconOnly` exige `aria-label`.
- Avatar: iniciales (máximo 2) o icono genérico si no hay nombre. Siempre decorativo.
- EmptyState: tarjeta centrada de 560 px máximo con icono, título `h1`, texto y acciones. Tonos `brand` y `danger`.
- StatusAlert: icono, título opcional y texto; tonos error, warning, success, info.
- Chip: etiqueta de 18 px para estados en filas ("Parcial").
- Skeleton: bloques `--skeleton` con brillo; reproducir la anatomía del contenido real.

## Iconografía

- `lucide-react`, trazo por defecto. Tamaños: 14 a 16 px en botones y filas, 18 a 20 px en navegación y adjuntos, 24 a 28 px en estados vacíos.
- Iconos decorativos con `aria-hidden`. Un icono sin texto visible necesita nombre accesible.

## Texto de interfaz

- Español neutro, tuteo, frases cortas. Sin jerga técnica (MSG/OLE/MAPI sólo si viene del mensaje de error del backend).
- Botones con verbo: "Abrir MSG", "Elegir archivos", "Reintentar", "Mostrar los 12".
- Datos ausentes: "Remitente desconocido", "Asunto no recuperado"; nunca placeholders genéricos.
