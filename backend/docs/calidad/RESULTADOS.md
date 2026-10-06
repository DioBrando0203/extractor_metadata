# Resultados de calidad

Registro: 2026-10-05 20:31:53 -05:00 (America/Lima).

| Comprobacion | Resultado |
|---|---|
| Backend pytest | 40 pruebas aprobadas. |
| Backend Ruff | Lint y formato correctos. |
| Frontend Vitest | 9 pruebas aprobadas. |
| Frontend lint y build | Correctos. |
| Frontend E2E | 5 pruebas aprobadas, incluida descarga y vista movil. |
| Descarga de adjunto | Prueba HTTP descarga un PDF sintetico, conserva sus bytes, nombre y MIME. |
| MSG de prueba principal | PDF recuperado de 2,635,579 bytes; descarga HTTP con SHA-256 identico al PDF extraido localmente. |
| Limpieza | El fixture confirma directorio temporal vacio tras extraer y descargar. |
| Peso | No hay rechazo fijo por peso; copia por bloques y timeout proporcional al MSG. |
| Recuperacion parcial | FAT truncada recuperable solo en copia temporal; adjuntos legibles conservados. |
| Privacidad | Sin correos reales en tests ni almacenamiento persistente. |

La suite backend muestra una advertencia de deprecacion de Starlette/TestClient con httpx; no falla ninguna prueba. La comprobacion manual del MSG proporcionado se mantuvo local y no se incorporo al repositorio.
