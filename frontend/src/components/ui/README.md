# Componentes generales

Presentacionales y reutilizables. Sin conocimiento de MSG, adjuntos ni de la API (P-04). Estilos en `global.css`, sección 3.

- `Button`: variantes primary, secondary, ghost y danger; tamaños md y sm; `iconOnly` exige `aria-label`.
- `Avatar`: iniciales con tono estable por nombre o icono genérico. Decorativo.
- `EmptyState`: tarjeta centrada para vacío, error o selección pendiente.
- `StatusAlert`: aviso con icono para error, warning, success e info. `role=alert` sólo en error.

Si un componente necesita tipos del dominio, va en `features/<dominio>/components`.
