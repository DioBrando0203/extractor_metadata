# Patrones de diseño (frontend)

Catálogo de patrones en uso: dónde están, cuándo aplicarlos y qué evitar. Antes de crear una estructura nueva, reutilizar una de estas.

## Componente de layout con huecos (slots)

Dónde: `components/layout/AppLayout.tsx` (`search`, `commands`, `list`, `children`, `overlay`).
Qué: el layout no conoce el dominio; `App` le pasa los paneles.
Cuándo: estructura repetida cuyo contenido cambia según la vista.

## Contenedor y presentación

Dónde: `App.tsx` y hooks (estado y efectos) frente a `MessageViewer`, `QueueRow`, `AttachmentTiles` (props a JSX).
Qué: la lógica vive en hooks y en `App`; los componentes de presentación reciben datos y callbacks.
Regla: un componente de presentación no llama a la API ni lee estado global.

## Hook personalizado para efectos

Dónde: `useExtractionQueue` (cola), `useWindowFileDrop` (eventos de ventana), `useAttachmentFiles` (caché de binarios).
Qué: encapsula efectos, refs y limpieza; devuelve una API estable (`useMemo`/`useCallback`).
Cuándo: el mismo efecto se usaría en más de un componente o la lógica supera unas 20 líneas.

## Caché con ciclo de vida

Dónde: `useAttachmentFiles`.
Qué: promesas por clave (`índice:variante`) y URLs `blob:` revocadas al desmontar; un fallo no queda en caché.
Cuándo: recursos costosos que se piden varias veces mientras se ve un mismo correo.

## Tabla de decisión (Strategy declarativa)

Dónde: `features/attachments/lib/viewerMode.ts`, `fileKind.ts`, iconos en `FileTypeIcon.tsx`.
Qué: un dato (extensión, MIME, fuente de miniatura) se traduce a un modo con conjuntos y mapas, no con `if` repartidos por componentes.
Cuándo: varias variantes de presentación según el tipo de dato.

## Fachada de API y normalización

Dónde: `lib/api.ts`.
Qué: único punto HTTP; tolera campos ausentes y valida datos sensibles (miniaturas sólo raster en base64).
Regla: la UI nunca recibe JSON crudo (P-02).

## Funciones puras

Dónde: `lib/mail.ts`, `lib/formatters.ts`, `features/*/lib`.
Qué: sin React ni efectos; se prueban sin DOM.

## Reinicio por clave

Dónde: `<MessageViewer key={id}>`, `<AttachmentPreview key={index}>`.
Qué: al cambiar de entidad, React monta de nuevo y el estado local parte limpio (P-10).

## Diálogo nativo

Dónde: `AttachmentViewer` con `<dialog>` y `showModal()`.
Qué: foco atrapado, fondo inerte y Esc gratis; el foco vuelve al botón que lo abrió.

## Antipatrones prohibidos

- Copiar estilos o lógica entre componentes en lugar de extraer un componente o una función.
- Componentes de más de 200 líneas o con más de un nivel de componentes internos sin separar archivos.
- `useEffect` para derivar datos que se pueden calcular en render.
- Pasar callbacks nuevos a listeners globales en cada render (usar ref, P-11).
- Lógica por tipo de archivo con `if` en JSX: usar `viewerMode` o `fileKind`.
- Utilidades genéricas `utils.ts`: cada función vive junto a su dominio.
