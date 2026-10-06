# Componentes de layout

`AppLayout.tsx`: cabecera de marca (buscador opcional), barra de apps, workspace con barra de comandos, bandeja y lector, botón volver para móvil y overlay. Comportamiento en SPEC-01.

- No conoce MSG ni la API; recibe los paneles como huecos (`search`, `commands`, `list`, `children`, `overlay`).
- `pane` decide qué panel se ve bajo 860 px; `contentKey` reinicia el scroll del lector.
