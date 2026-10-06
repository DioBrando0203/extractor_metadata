# Frontend local

Cliente React que abre archivos `.msg` y los presenta como un lector de correo (bandeja y panel de lectura), sin usar marca ni assets de Microsoft. Toda la documentación está en [docs/README.md](docs/README.md); agentes IA: empezar por [docs/GUIA_IA.md](docs/GUIA_IA.md).

```bash
npm install
npm run dev
```

Verificación completa: `npm run format:check && npm run build && npm run lint && npm test && npm run test:e2e`.
Revisión visual en cinco anchos: `npm run test:visual` (capturas en `test-results/capturas/`).

`VITE_API_URL` sólo para apuntar a otro backend local; por defecto `http://127.0.0.1:8000/api` en desarrollo y `/api` en el build servido por el backend.
