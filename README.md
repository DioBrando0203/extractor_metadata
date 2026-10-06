# Lector local de correos MSG

Elija o arrastre un archivo `.msg` para leer el correo y descargar los archivos adjuntos que aun se puedan abrir. La aplicacion esta pensada para personas que solo quieren ver su correo: la pantalla principal evita diagnosticos tecnicos y muestra Resumen, Cuerpo y Adjuntos.

Todo funciona en su equipo. No hay login, base de datos, nube, telemetria ni historial. El MSG original no se modifica: el backend usa una copia temporal que borra al terminar. Para descargar un adjunto, el navegador reenvia el MSG que conserva en memoria y el servidor crea otra copia temporal solo durante esa descarga.

## Inicio en Windows

Requiere Python 3.11+ y Node LTS.

```powershell
py -m venv backend/.venv
backend/.venv/Scripts/python.exe -m pip install -c backend/requirements.lock -e "backend[dev]"
cd frontend
npm ci
npm run build
cd ..
py iniciar.py
```

Abra `http://127.0.0.1:8000`. Tambien puede usar `iniciar.bat` despues de preparar dependencias.

## Desarrollo

```powershell
cd backend
.venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload --no-access-log
```

```powershell
cd frontend
npm run dev
```

La interfaz de desarrollo usa `http://127.0.0.1:5173`; OpenAPI local esta en `http://127.0.0.1:8000/docs`.

## Cobertura y limites

- Adjuntos legibles se pueden descargar, incluidos imagenes, PDF, Word, Excel y otros formatos cuyos bytes sigan disponibles.
- No existe un limite fijo por peso para el MSG o sus adjuntos; archivos grandes pueden tardar mas.
- Si una parte esta danada, se muestra lo que siga legible. No se afirma reparar el archivo original ni recuperar datos ya perdidos.
- No se ejecutan macros ni HTML activo. DWG tiene reconocimiento basico, no interpretacion profunda.

## Verificacion

```powershell
cd backend
.venv/Scripts/python.exe -m pytest
.venv/Scripts/python.exe -m ruff check app tests
.venv/Scripts/python.exe -m ruff format --check app tests

cd ../frontend
npm run build
npm run lint
npm test
```

Documentacion de continuidad: [guia de agentes](AGENTS.md), [backend](backend/docs/ARQUITECTURA.md), [frontend](frontend/docs/ARQUITECTURA.md) y [requerimientos](backend/docs/REQUERIMIENTOS.md).
