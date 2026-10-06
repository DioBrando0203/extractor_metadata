# Stack del frontend

Versiones exactas en `package.json` y `package-lock.json`. No usar rangos (`^`, `~`).

## Ejecución

- React 19: UI declarativa. Sin librerías de estado global; el estado cabe en un hook y en `App`.
- TypeScript 5.9 estricto: `tsc --noEmit` forma parte del build.
- Vite 8: dev server en `127.0.0.1:5173` y build a `dist/`, que FastAPI sirve en el mismo origen.
- Tailwind CSS 4 vía `@tailwindcss/vite`: sólo se aprovecha su preflight (reset). Los estilos propios están en `global.css` con tokens; no se usan utilidades en JSX (ADR-08).
- lucide-react: iconos SVG en línea, sin peticiones de red.

## Pruebas y herramientas

- Vitest 5 + jsdom + React Testing Library + jest-dom: unitarias y de componente.
- Playwright 1.63 con Chromium: E2E funcional y visual. Instalar navegador con `npx playwright install chromium`.
- ESLint 10 con typescript-eslint, react-hooks y react-refresh.
- Prettier 3: `printWidth` 110, sin punto y coma, comillas simples, coma final.

## Restricciones

- Sin fuentes web, CDNs, analítica ni dependencias que llamen a la red.
- Sin sanitizadores HTML ni visores de documentos mientras ADR-07 siga vigente.
- Tras cambiar dependencias: `npm audit --omit=dev` y `npm audit` sin vulnerabilidades; registrar el motivo aquí.

## Entorno verificado

- Windows 11, Node 24, Chromium de Playwright.
- `VITE_API_URL` opcional; por defecto `http://127.0.0.1:8000/api` en desarrollo y `/api` en build.
