# Reglas de estilos y diseño

Valores y uso de tokens en `estilos/SISTEMA_VISUAL.md`.

## Tokens

- E-01: todo color, tamaño de fuente, espaciado, radio, sombra y duración sale de un token de `:root`. Prohibidos hex, rgb o px sueltos en reglas de componentes, salvo ajustes ópticos de 1 a 6 px (gaps entre icono y texto, indicadores) y dimensiones intrínsecas de componente listadas en `SISTEMA_VISUAL.md`, sección Dimensiones de layout.
- E-02: antes de crear un token, buscar uno existente. Un token nuevo se documenta en `SISTEMA_VISUAL.md` en el mismo cambio.
- E-03: `--subtle` nunca se usa para texto. Texto secundario usa `--muted` como mínimo.

## Organización del CSS

- E-04: `global.css` mantiene el orden de secciones numeradas. Un bloque nuevo va en la sección de su módulo.
- E-05: especificidad baja y plana. Máximo tres clases por selector. Sin `!important` ni selectores por id.
- E-06: los estados se expresan con `is-*`, `aria-*` o `data-*`, no con clases nuevas por cada combinación.
- E-07: media queries agrupadas en la sección 9 por breakpoint, de mayor a menor ancho, salvo `prefers-reduced-motion` junto a su animación.

## Layout

- E-08: ningún contenido provoca scroll horizontal del documento. En flex y grid, los hijos con texto llevan `min-width: 0`; columnas con `minmax(0, 1fr)`.
- E-09: textos de longitud variable (asuntos, nombres de archivo, correos) se recortan con elipsis o usan `overflow-wrap: anywhere`. Elegir explícitamente.
- E-10: el contenido de lectura respeta `--reading-max`. Nada se estira a todo el ancho de un monitor grande.
- E-11: cada panel tiene su propio scroll; el `body` no hace scroll.

## Interacción y accesibilidad visual

- E-12: contraste AA: 4.5:1 en texto normal, 3:1 en texto grande e iconos funcionales.
- E-13: foco visible en todo elemento interactivo con `--focus`. No eliminar `outline` sin sustituto.
- E-14: todo control interactivo tiene estado hover y, si aplica, active y disabled. Hover nunca es la única pista.
- E-15: objetivos táctiles de al menos 28 px con ratón y 36 px con puntero táctil (`pointer: coarse`).
- E-16: el color nunca es la única señal: estados con icono o texto (chip "Parcial", "No se pudo leer").
- E-17: transiciones de 120 ms en color, fondo y borde. Animaciones continuas sólo con `prefers-reduced-motion: no-preference`.

## Marca

- E-18: no usar logos, iconos propietarios, nombres de producto ni capturas de Microsoft. El titular de la portada puede mencionar Outlook como referencia del problema que resuelve.
