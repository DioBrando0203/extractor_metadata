# Guía breve para retomar el proyecto

## ¿Qué podemos continuar?

Si el usuario pregunta qué sigue, qué falta o qué podemos continuar: leer `backend/docs/REQUERIMIENTOS.md`, sección "Pendientes por revisar" (IDs PEN-xx), y responder con esa lista en orden de prioridad (alta, media, baja), indicando por cada pendiente su situación y qué haría falta. No inventar pendientes fuera de esa lista sin revisarla primero; si se descubre uno nuevo, agregarlo allí con su ID antes de trabajarlo. Al terminar uno, actualizar su estado y la bitácora.

Estado: proyecto cerrado momentáneamente desde el 2026-10-08. No empezar trabajo nuevo sin que el usuario lo pida; al retomar, partir del "Estado del proyecto" de `REQUERIMIENTOS.md`.

Antes de modificar, leer este archivo y la guía del lado afectado (metodología SDD: spec, plan, código, prueba, registro):
- Backend: `backend/docs/README.md` y `backend/docs/GUIA_IA.md`; reglas `PY-xx` y `patrones/PATRONES.md`.
- Frontend: `frontend/docs/README.md` y `frontend/docs/GUIA_IA.md`; reglas `P-xx`, `E-xx`, `C-xx` y `patrones/PATRONES.md`.
- `backend/docs/REQUERIMIENTOS.md`: alcance, cobertura y backlog priorizado de pendientes (PEN-xx). Revisarlo antes de proponer trabajo nuevo.

## Requisitos permanentes

Aplicación LOCAL Linux/Windows; el acceso desde otras PCs de la red es opcional y explícito (ADR-B12). Sin BD, login, usuarios registrados, nube ni telemetría.
El usuario arrastra o elige MSG; ve el correo como en Outlook, ve de frente imágenes, PDF y miniaturas de planos, consulta los detalles de cada adjunto y lo descarga.
Archivos de sesión sólo en memoria del navegador y temporales efímeros del backend.
Se elimina el temporal al finalizar, incluido error/timeout. Nunca modificar el original.
No afirmar que se reparó corrupción física ni que se puede interpretar cualquier DWG.

## Arquitectura y reglas

`frontend/`: React/TS/Vite, Fluent 2 (tokens e iconos MIT), features autónomas y UI reutilizable fuera del dominio.
`backend/`: FastAPI, rutas delgadas, paquetes `msg/`, `metadata/`, `previews/` y proceso aislado.
Código limpio en ambos lados: un módulo, una responsabilidad; archivos cortos (Python ≤ 300, TS ≤ 200, CSS ≤ 250 líneas); funciones cortas; reutilizar antes de crear; patrones documentados antes que soluciones ad hoc.
Mantener docs de arquitectura, specs, ADR, reglas, bloqueos, calidad y bitácora sincronizadas con el código.
Docs escritos para IA: listas e IDs citables, sin tablas ni separadores.
Bitácora: fecha/hora de America/Lima, tarea, estado y evidencia. No inventar ejecución de pruebas.
No almacenar correos de usuarios como fixtures; usar MSG sintéticos generados en tests.
Commits y push directamente en `main`.

## Verificación

Backend (desde backend): `.venv/bin/python -m pytest`, `.venv/bin/python -m ruff check app tests`, `ruff format --check`.
Frontend (desde frontend): `npm run format:check`, `npm run build`, `npm run lint`, `npm test`, `npm run test:e2e`, `npm run test:visual`.
Verificar flujo HTTP + navegador al cambiar contrato o carga, con el backend reiniciado. En Windows usar `.venv/Scripts/python.exe`.
Correos de prueba sintéticos para revisar a mano: `backend/tests/generar_ejemplos.py <carpeta>`.
No escribir código con escapes (`\n`, `\d`, `\u…`) desde heredocs de shell: usar el editor o un archivo de script (B-13).

Los docs reducen el trabajo de orientación en futuras sesiones; no eliminan la necesidad de inspeccionar
el código afectado ni el consumo de contexto de un agente.
