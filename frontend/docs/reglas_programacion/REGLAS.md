# Reglas de programación

Obligatorias salvo que digan "preferir". Citar el ID en revisiones y en la bitácora.

## Tipado y estructura

- P-01: TypeScript estricto. Prohibido `any`, `as unknown as` y aserciones `!` sobre datos del backend. Pasar el valor ya comprobado como prop tipada.
- P-02: toda llamada HTTP vive en `lib/api.ts`. Los componentes reciben datos normalizados (`lib/types.ts`), nunca `Response` ni JSON crudo.
- P-03: una feature no importa la `lib`, hooks ni estado de otra feature. Única excepción vigente: ADR-05.
- P-04: `components/ui` y `components/layout` no conocen MSG, adjuntos ni la API. Si un componente necesita tipos del dominio, va en `features/<dominio>/components`.
- P-05: nunca `dangerouslySetInnerHTML`, `innerHTML` ni evaluación de contenido del correo.
- P-06: lógica pura (parseo, formato, clasificación) en funciones sin React en `lib/` o `features/<dominio>/lib/`, con pruebas unitarias.
- P-07: un componente por responsabilidad. Máximo 200 líneas por archivo; al pasar de 150 o al mezclar estados de carga, error y éxito, separar en archivos (ejemplo: `AttachmentList`, `AttachmentTiles`, `AttachmentViewer`, `AttachmentPreview`, `AttachmentDetails`).

## Estado y efectos

- P-08: estado de sesión sólo en memoria React. Prohibido localStorage, sessionStorage, IndexedDB y cookies para archivos o resultados.
- P-09: efectos sólo para sincronizar con sistemas externos (eventos de `window`, scroll, DOM). Derivar datos en render.
- P-10: usar `key` para reiniciar estado local al cambiar de entidad (p. ej. `MessageViewer key={item.id}`), no efectos que lo limpien.
- P-11: callbacks pasados a listeners globales se leen desde una ref actualizada en un efecto, no se re-suscriben en cada render.
- P-12: liberar recursos: `URL.revokeObjectURL` tras descargar, remover listeners en el cleanup.

## Accesibilidad en código

- P-13: elementos interactivos son `<button>` o `<a>` reales. Prohibido `onClick` en `div` o `span`.
- P-14: botones con icono solo llevan `aria-label`; iconos decorativos `aria-hidden="true"`.
- P-15: no anidar botones. Acciones secundarias de una fila se posicionan fuera del botón principal (ver reintentar en la bandeja).
- P-16: estados de carga con `role="status"` o `aria-busy`; errores accionables con `role="alert"`.

## Estilo de código

- P-17: Prettier (`printWidth` 110, sin punto y coma, comillas simples) y ESLint sin errores ni warnings.
- P-18: nombres en inglés; textos visibles y comentarios en español.
- P-19: comentar el porqué, no el qué. Sin comentarios que repitan el código.
- P-20: clases CSS en kebab-case con patrón bloque, `bloque__elemento`, `bloque--variante`, estados con `is-*` o atributos ARIA/data.
- P-21: no usar utilidades Tailwind en JSX; los estilos viven en `global.css` (ADR-08). Importar iconos por nombre (`ArrowDownload20Regular`), nunca el paquete completo.

## Reutilización y patrones

- P-23: antes de crear un componente, hook o función, buscar uno existente (`rg`) y ampliarlo si encaja. Catálogo en `patrones/PATRONES.md`.
- P-24: regla de tres: la tercera copia de un bloque de JSX, estilo o lógica obliga a extraerlo.
- P-25: componentes genéricos en `components/ui` con API mínima y nombres de Fluent (`variant`, `size`); nunca duplicar un botón o un aviso con estilos propios.
- P-26: lógica con efectos en hooks (`use*`) que devuelven objetos estables con `useMemo`/`useCallback`.
- P-27: decisiones por tipo de dato en tablas (`viewerMode`, `fileKind`), no en condicionales dentro de JSX.
- P-28: funciones auxiliares y handlers de máximo 40 líneas; cuerpo de un componente de máximo 120 líneas. Extraer subcomponentes con nombre en vez de ternarios anidados de más de dos niveles (ejemplo: `ReaderContent` en `App.tsx`).
- P-29: props explícitas y tipadas; máximo 7 props de datos o callbacks por componente. Los huecos `ReactNode` de un layout (`search`, `commands`, `list`, `overlay`) no cuentan. Con más, agrupar en un objeto con nombre o dividir el componente.
- P-30: sin estado duplicado: lo que se deriva de otras props o estado se calcula en render.

## Dependencias

- P-22: versiones exactas en `package.json`. Toda dependencia nueva se justifica en `tecnologias/STACK.md` y pasa `npm audit`. Iconos sólo de `@fluentui/react-icons` (ADR-09).
