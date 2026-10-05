# Frontend local

Cliente React para cargar un MSG y presentar un lector de correo inspirado en patrones conocidos, sin usar marca, activos ni afirmación de ser Outlook. Consulte [docs/ARQUITECTURA.md](docs/ARQUITECTURA.md).

```bash
npm install
npm run dev
```

Validación completa: `npm run format:check && npm run build && npm run lint && npm test && npm run test:e2e`.

Configure `VITE_API_URL` sólo para un backend local; el valor por defecto es `http://localhost:8000/api`.
