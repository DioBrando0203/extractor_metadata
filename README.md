# Inspector MSG local

Aplicación de escritorio mediante navegador: arrastre o elija archivos MSG y consulte el mensaje,
encabezados, propiedades y metadatos de los adjuntos. Sin login, BD ni historial persistente.
Los resultados permanecen en la sesión; los temporales del backend se borran al terminar cada análisis.

## Instalación Linux

Requiere Python 3.11–3.14 y Node LTS (instalado con nvm). Desde la raíz:

```bash
. "$HOME/.nvm/nvm.sh"
nvm install --lts
python3 -m venv backend/.venv
backend/.venv/bin/python -m pip install -c backend/requirements.lock -e 'backend[dev]'
cd frontend
npm ci
npm run build
cd ..
python3 iniciar.py
```

Abre automáticamente `http://127.0.0.1:8000`. Para evitar abrir el navegador: `python3 iniciar.py --sin-navegador`.
Ctrl+C detiene el servicio. Sólo escucha en la máquina local.
Si ya está en ejecución, el lanzador abre la interfaz de la instancia existente.

## Instalación Windows (PowerShell)

Instale Python 3.11 o posterior y Node LTS. No copie el entorno `.venv` de Linux; créelo en Windows.

```powershell
py -m venv backend/.venv
backend/.venv/Scripts/python.exe -m pip install -c backend/requirements.lock -e "backend[dev]"
cd frontend
npm ci
npm run build
cd ..
py iniciar.py
```

Tras preparar el proyecto, también puede abrir `iniciar.bat`. La compatibilidad se diseñó con rutas
y procesos multiplataforma; falta validación nativa en un equipo Windows.

## Desarrollo

Dos terminales:

```bash
cd backend
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload --no-access-log
```

```bash
. "$HOME/.nvm/nvm.sh"
cd frontend
npm run dev
```

La interfaz de desarrollo abre en `http://127.0.0.1:5173`. OpenAPI local: `http://127.0.0.1:8000/docs`.

## Cobertura real

- MSG: correo, cuerpo de texto, encabezados, propiedades MAPI/OLE, adjuntos y recuperación parcial.
- Imágenes: formato, dimensiones, modo y EXIF. PDF: propiedades, páginas y cifrado.
- Office OOXML (XLSX/DOCX/PPTX): propiedades del documento; Excel incluye nombres de hojas.
- DXF: versión de formato, unidades y capas. DWG: firma y versión básica; sin propiedades profundas.
- Cualquier otro adjunto: nombre, tamaño, extensión y firma disponible, con advertencia de cobertura.
- ExifTool opcional amplía únicamente los formatos que soporta; no se promete DWG mediante ExifTool.

Instale ExifTool en el PATH del sistema si necesita metadata adicional. En Linux suele corresponder al
paquete `libimage-exiftool-perl`; en Windows use su distribución oficial y reinicie el servicio.
No hace falta ExifTool para la lectura nativa.

## Límites y privacidad

100 MB por MSG; 50 MB para análisis profundo de un adjunto; 200 adjuntos; 150 MB acumulados de adjuntos.
Más de 10 MB produce advertencia, no rechazo. Cuerpo visible hasta 100.000 caracteres; valores largos
truncados de forma explícita. El proceso de lectura tiene timeout de 90 segundos y memoria limitada en Linux.
La API nunca devuelve binarios ni ejecuta macros/HTML. Renombrar evita problemas de ruta, no repara
corrupción física; esta aplicación analiza una copia de nombre corto sin alterar el archivo original.

## Continuidad y pruebas

[Guía para agentes](AGENTS.md) · [Backend](backend/docs/ARQUITECTURA.md) ·
[Frontend](frontend/docs/ARQUITECTURA.md) · [Requisitos y pendientes](backend/docs/REQUERIMIENTOS.md).

```bash
cd backend
.venv/bin/python -m pytest
.venv/bin/ruff check app tests
.venv/bin/ruff format --check app tests
```

```bash
cd frontend
npm run build
npm run lint
npm test
npm run test:e2e
```
