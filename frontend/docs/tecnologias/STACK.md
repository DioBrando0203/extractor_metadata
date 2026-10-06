# Stack del frontend

Versiones exactas en `package.json` y `package-lock.json`. No usar rangos (`^`, `~`).

## Ejecución

- React 19: UI declarativa. Sin librerías de estado global; el estado cabe en un hook y en `App`.
- TypeScript 5.9 estricto: `tsc --noEmit` forma parte del build.
- Vite 8: dev server en `127.0.0.1:5173` y build a `dist/`, que FastAPI sirve en el mismo origen.
- Tailwind CSS 4 vía `@tailwindcss/vite`: sólo su preflight (reset) y el empaquetado de `@import`. Estilos propios en `src/app/styles/*.css` con tokens de Fluent 2; sin utilidades en JSX (ADR-08).
- @fluentui/react-icons 2.0.343 (MIT): iconos de Fluent 2, los de Outlook. Se importan por nombre; el bundle sólo incluye los usados. Usa Griffel para estilos en tiempo de ejecución, sin red. Sustituye a lucide-react (ADR-09).

## Pruebas y herramientas

- Vitest 5 + jsdom + React Testing Library + jest-dom: unitarias y de componente.
- Playwright 1.63 con Chromium: E2E funcional (`test:e2e`) y visual (`test:visual`, etiqueta `@visual`). Instalar navegador con `npx playwright install chromium`.
- ESLint 10 con typescript-eslint, react-hooks y react-refresh.
- Prettier 3: `printWidth` 110, sin punto y coma, comillas simples, coma final.

## Restricciones

- Sin fuentes web, CDNs, analítica ni dependencias que llamen a la red.
- Sin sanitizadores HTML (ADR-07) ni librerías de render de documentos (pdf.js, visores DWG): se usan los visores nativos del navegador y las miniaturas del backend (ADR-11).
- Tras cambiar dependencias: `npm audit --omit=dev` y `npm audit` sin vulnerabilidades; registrar el motivo aquí.

## Entorno verificado

- Windows 11, Node 24, Chromium de Playwright.
- `VITE_API_URL` opcional; por defecto `http://127.0.0.1:8000/api` en desarrollo y `/api` en build.
