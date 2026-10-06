# Componentes de layout

`AppLayout.tsx`: barra superior, rail de navegación, columna de bandeja opcional, lector (`main#reader`), botón volver para móvil y overlay. Comportamiento en SPEC-01.

- No conoce MSG ni la API; recibe la bandeja, el contenido y el overlay como props.
- `pane` decide qué panel se ve bajo 860 px; `contentKey` reinicia el scroll del lector.
