# Reglas de estilos y diseño

Valores y uso de tokens en `estilos/SISTEMA_VISUAL.md`. Base: Fluent 2, el sistema de diseño público de Microsoft que usa Outlook (ADR-09).

## Tokens

- E-01: todo color, tamaño de fuente, interlineado, espaciado, radio, sombra y duración sale de un token de `tokens.css`. Prohibidos hex, rgb o px sueltos en reglas de componentes, salvo ajustes ópticos de 1 a 6 px y dimensiones intrínsecas listadas en `SISTEMA_VISUAL.md`.
- E-02: antes de crear un token, buscar uno existente. Un valor nuevo se toma de la rampa de Fluent 2 y se documenta en `SISTEMA_VISUAL.md` en el mismo cambio.
- E-03: texto siempre con `--fg-1`, `--fg-2` o `--fg-3` (todos AA). Nunca grises más claros para texto.

## Organización del CSS

- E-04: un archivo por módulo en `src/app/styles/`, importado desde `global.css` en orden: tokens, base, ui, layout, features, viewer, help y responsive al final.
- E-05: máximo 250 líneas por archivo CSS; al superarlas, dividir por responsabilidad (ejemplo: `ui-controls.css` y `ui-display.css`).
- E-06: especificidad baja y plana. Máximo tres clases por selector. Sin `!important` ni selectores por id.
- E-07: estados con `is-*`, `aria-*` o `data-*`, no con clases nuevas por combinación.
- E-08: media queries de tamaño en `responsive.css`, agrupadas por breakpoint de mayor a menor; `prefers-reduced-motion` y `hover: hover` junto a la regla que modifican.
- E-09: estilos de un componente nuevo en el archivo de su módulo con el patrón `bloque__elemento--variante`.

## Layout

- E-10: ningún contenido provoca scroll horizontal del documento. En flex y grid, hijos con texto con `min-width: 0`; columnas con `minmax(0, 1fr)`.
- E-11: textos variables (asuntos, nombres de archivo, correos) con elipsis o `overflow-wrap: anywhere`, elegido explícitamente.
- E-12: la lectura respeta `--reading-max`; nada se estira a todo el ancho de un monitor grande.
- E-13: cada panel tiene su propio scroll; el `body` no hace scroll. Paneles blancos con `--radius-xl` sobre `--bg-4`, separados por `--pane-gap`.

## Interacción y accesibilidad visual

- E-14: contraste AA: 4.5:1 en texto normal, 3:1 en texto grande e iconos funcionales.
- E-15: foco visible en todo elemento interactivo (contorno oscuro con halo claro de Fluent; blanco sobre fondos de marca u oscuros).
- E-16: todo control tiene hover y, si aplica, pressed y disabled. Hover nunca es la única pista (en táctil las acciones ocultas por hover se muestran siempre).
- E-17: objetivos táctiles de 24 px con ratón y 32 a 40 px con puntero táctil (`pointer: coarse`).
- E-18: el color nunca es la única señal: estados con icono o texto.
- E-19: transiciones de 100 a 200 ms con `--curve-easy-ease`; animaciones continuas sólo con `prefers-reduced-motion: no-preference`.

## Marca

- E-20: se usan tokens e iconos de Fluent 2 (MIT). Prohibido el logotipo, el nombre "Outlook" como marca de la app, capturas o iconos de producto de Microsoft. El titular de la portada puede mencionar Outlook como referencia del problema.
