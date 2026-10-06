# Resultados de calidad

Registro: 2026-10-05 20:13:35 -05:00 (America/Lima).

| Comprobacion       | Resultado                                                                                 |
| ------------------ | ----------------------------------------------------------------------------------------- |
| `npm run build`    | TypeScript y build Vite correctos.                                                        |
| `npm run lint`     | ESLint correcto.                                                                          |
| `npm test`         | 9 pruebas aprobadas.                                                                      |
| `npm run test:e2e` | 5 pruebas aprobadas.                                                                      |
| Descarga visible   | Playwright carga un MSG sintetico, pulsa Descargar y verifica bytes y nombre `plano.dwg`. |
| Vista simple       | E2E confirma que no aparecen `Observaciones del extractor` ni pestana Metadatos.          |
| Movil              | E2E a 320 y 390 px confirma boton Descargar visible y sin desborde horizontal.            |
| Mismo origen       | E2E confirma el build servido por FastAPI y extraccion local.                             |

Entorno: Windows, Node v24.21.0, Chromium Playwright instalado localmente. Los fixtures se generan desde `backend/tests/msg_factory.py`; no contienen correos privados. Las capturas y descargas de prueba viven en directorios ignorados.
