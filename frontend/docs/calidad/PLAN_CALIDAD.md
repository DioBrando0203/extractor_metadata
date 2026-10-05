# Plan de calidad

Verificar `npm run build`, `npm run lint`, `npm test`, `npm run test:e2e` y `npm run format:check` antes de integrar. Las pruebas unitarias cubren normalización del contrato/API y la cola secuencial (incluido error, reintento y limpieza durante una petición pendiente); las de componente cubren pestañas y nuevo análisis; la E2E cubre entrada y ayuda.

Revisar contraste, foco, ancho 320 px, la bandeja horizontal móvil, exportación JSON, archivos mayores a 10 MB y que no se renderice HTML no confiable. El E2E real cubre selección múltiple, MSG corrupto seguido de válido, cuerpo/encabezados/adjuntos, exportación JSON, limpieza y móvil 320/390 px. El corpus >10 MB se verifica en backend. Consultar RESULTADOS.md para la última ejecución.

## E2E con servicio local

Antes de `npm run test:e2e`, ejecutar `npm run build`: el lanzador unificado del backend sirve el contenido de `dist`. Playwright arranca o reutiliza dos servidores: el lanzador local en `http://127.0.0.1:8000` (confirmado mediante `/api/health`) y Vite en el puerto 5173. En Linux invoca `python3 ../iniciar.py --sin-navegador`; en Windows usa `py ../iniciar.py --sin-navegador`. No usar servicios externos ni fixtures con correo real.
