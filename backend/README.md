# Backend local

Lea [docs/ARQUITECTURA.md](docs/ARQUITECTURA.md) y [docs/REQUERIMIENTOS.md](docs/REQUERIMIENTOS.md)
antes de cambiar el contrato o el flujo de extracción.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -c requirements.lock -e '.[dev]'
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --no-access-log
```

Windows: usar `.venv/Scripts/python.exe`. OpenAPI `/docs`, salud `/api/health`,
extracción `POST /api/messages/extract` (multipart, campo `file`).
El build frontend se sirve en `/` si existe al arrancar.
