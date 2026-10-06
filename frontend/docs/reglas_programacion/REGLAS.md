# Reglas de programación

Obligatorias salvo que digan "preferir". Citar el ID en revisiones y en la bitácora.

## Tipado y estructura

- P-01: TypeScript estricto. Prohibido `any`, `as unknown as` y aserciones `!` sobre datos del backend. Pasar el valor ya comprobado como prop tipada.
- P-02: toda llamada HTTP vive en `lib/api.ts`. Los componentes reciben datos normalizados (`lib/types.ts`), nunca `Response` ni JSON crudo.
- P-03: una feature no importa la `lib`, hooks ni estado de otra feature. Única excepción vigente: ADR-05.
- P-04: `components/ui` y `components/layout` no conocen MSG, adjuntos ni la API. Si un componente necesita tipos del dominio, va en `features/<dominio>/components`.
- P-05: nunca `dangerouslySetInnerHTML`, `innerHTML` ni evaluación de contenido del correo.
- P-06: lógica pura (parseo, formato, clasificación) en funciones sin React en `lib/` o `features/<dominio>/lib/`, con pruebas unitarias.
- P-07: un componente por responsabilidad. Si un archivo pasa de unas 200 líneas o mezcla estados de carga, error y éxito, separar subcomponentes.

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
- P-21: no usar utilidades Tailwind en JSX; los estilos viven en `global.css` (ADR-08).

## Dependencias

- P-22: versiones exactas en `package.json`. Toda dependencia nueva se justifica en `tecnologias/STACK.md` y pasa `npm audit`.
