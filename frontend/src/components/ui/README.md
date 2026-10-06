# Componentes generales

Presentacionales y reutilizables, con nombres y apariencias de Fluent 2. Sin conocimiento de MSG, adjuntos ni de la API (P-04). Estilos en `ui-controls.css` y `ui-display.css`.

- `Button`: `primary`, `secondary`, `subtle`, `danger`; tamaños `md` (32) y `sm` (24); `iconOnly` exige `aria-label`.
- `SearchBox`: buscador con lupa, borrar y Esc.
- `Tabs`: TabList con flechas, Inicio y Fin; el padre renderiza el `tabpanel` con el `panelId`.
- `Avatar`: iniciales con tono estable de la paleta de personas o icono genérico. Decorativo.
- `StatusAlert`: MessageBar de Fluent para error, warning, success e info. `role=alert` sólo en error.
- `EmptyState`: icono, título, texto y acciones para vacío, error o selección pendiente.
- `Spinner`: anillo de progreso; con `label` se anuncia; `tone="inverted"` para fondos oscuros.

Antes de crear otro componente aquí, comprobar que al menos dos features lo necesitan (P-24).
