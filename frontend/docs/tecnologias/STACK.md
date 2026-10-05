# Stack del frontend

- React 19 + TypeScript 5.9, compilación estricta.
- Vite 8 y Tailwind CSS 4; los tokens y reglas de interfaz se definen en `src/app/styles/global.css`.
- Vitest + React Testing Library para unidad/componente; Playwright para recorrido E2E.
- ESLint 10, Prettier y lockfile npm para reproducibilidad.

Las versiones están fijadas exactamente en `package.json`. Tras cambios de dependencias ejecutar `npm audit --omit=dev` y `npm audit`; ambos deben permanecer sin vulnerabilidades.
