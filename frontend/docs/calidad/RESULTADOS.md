# Resultados de calidad

Registro: 2026-10-05 18:21:49 -05:00 (America/Lima).

| Comprobación                          | Resultado                                                                         |
| ------------------------------------- | --------------------------------------------------------------------------------- |
| npm run build                         | Compilación TypeScript estricta y build Vite correctos.                           |
| npm run lint                          | ESLint correcto.                                                                  |
| npm test                              | 8 pruebas aprobadas en 4 archivos.                                                |
| npm run format:check                  | Prettier correcto.                                                                |
| npm audit y npm audit --omit=dev      | 0 vulnerabilidades reportadas.                                                    |
| E2E ayuda/cola/inspección/exportación | 4 pruebas aprobadas: inicial/ayuda, cola real corrupto+válido y móvil 320/390 px. |
| E2E arranque unificado                | Prueba adicional del build servido por FastAPI y carga en el mismo origen.        |
| Contraste visual                      | Texto secundario #52677d: 5.84:1 sobre blanco; rutas largas quiebran en móvil.    |
| Revisión visual                       | Capturas desktop y móvil inspeccionadas durante la sesión.                        |

Entorno: Node v24.21.0 (nvm), Chromium Playwright. Dependencias exactas en package-lock.json.
Backend real en 127.0.0.1:8000, Vite en 127.0.0.1:5173 durante E2E.
Fixtures generados desde backend/tests/msg_factory.py, sin correos privados.
Los screenshots se generan en test-results/ (ignorado); no se guardan resultados de usuarios.
La revisión de contraste no constituye una auditoría completa de accesibilidad con tecnología asistiva.
Windows todavía necesita verificación nativa.
