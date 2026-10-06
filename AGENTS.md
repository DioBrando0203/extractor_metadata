# Guía breve para retomar el proyecto

Antes de modificar, leer este archivo y la arquitectura del lado afectado:
- `backend/docs/ARQUITECTURA.md`
- `frontend/docs/README.md` y `frontend/docs/GUIA_IA.md`: índice, protocolo SDD y definición de terminado del frontend.
- `frontend/docs/ARQUITECTURA.md`
- `backend/docs/REQUERIMIENTOS.md`: alcance, cobertura y pendientes reales.

## Requisitos permanentes

Aplicación LOCAL Linux/Windows. Sin BD, login, usuarios registrados, nube ni telemetría.
El usuario arrastra o elige MSG; ve correo, propiedades y metadata de sus adjuntos.
Archivos de sesión sólo en memoria del navegador y temporales efímeros del backend.
Se elimina el temporal al finalizar, incluido error/timeout. Nunca modificar el original.
No afirmar que se reparó corrupción física ni que se puede interpretar cualquier DWG.

## Arquitectura y reglas

`frontend/`: React/TS/Vite/Tailwind, features autónomas y UI reutilizable fuera del dominio.
`backend/`: FastAPI, rutas delgadas, servicios, modelos, extractores y proceso aislado.
Estilos y tokens globales; componentes específicos dentro de cada feature.
Mantener docs de arquitectura, reglas, bloqueos, calidad y bitácora sincronizadas con código.
Bitácora: fecha/hora de America/Lima, tarea, estado y evidencia. No inventar ejecución de pruebas.
No almacenar correos de usuarios como fixtures; usar MSG sintéticos generados en tests.

## Verificación

Backend (desde backend): `.venv/bin/python -m pytest`, `.venv/bin/ruff check app tests`.
Frontend (desde frontend): `npm run build`, `npm run lint`, `npm test`.
Verificar flujo HTTP + navegador al cambiar contrato o carga. En Windows usar `.venv/Scripts/python.exe`.

Los docs reducen el trabajo de orientación en futuras sesiones; no eliminan la necesidad de inspeccionar
el código afectado ni el consumo de contexto de un agente.
