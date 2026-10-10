# Arranque de Inspector MSG en Windows Server

## Primera instalación

Requiere Python 3.11 o superior y Node.js LTS. Ejecutar PowerShell desde la
raíz del proyecto:

```powershell
py -3 -m venv backend\.venv
backend\.venv\Scripts\python.exe -m pip install -c backend\requirements.lock -e "backend[dev]"

cd frontend
npm ci
npm run build
cd ..
```

Para usar el conversor KML/KMZ, instalar también GDAL y comprobar que
`ogr2ogr.exe` esté disponible en el `PATH`.

## Servidor Windows para la red

Crear la configuración a partir del ejemplo:

```powershell
Copy-Item backend\.env.example backend\.env
```

Editar `backend\.env` y agregar la IP del servidor. Ejemplo:

```text
APP_ALLOWED_HOSTS=localhost,127.0.0.1,192.168.1.20
APP_ALLOWED_ORIGINS=http://192.168.1.20:8000
```

Después de compilar el frontend, iniciar la aplicación desde la raíz:

```powershell
backend\.venv\Scripts\python.exe -m uvicorn app.main:app --env-file backend\.env --host 0.0.0.0 --port 8000 --no-access-log
```

Abrir desde otra PC:

```text
http://IP_DEL_SERVIDOR:8000
```

Permitir el puerto `8000` en el firewall de Windows Server, si no está
permitido:

```powershell
New-NetFirewallRule -DisplayName "Inspector MSG 8000" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow
```

El backend sirve el frontend compilado desde `frontend/dist`. Después de cada
actualización del código hay que ejecutar `npm run build` y reiniciar Uvicorn.

## Desarrollo local en Windows

Backend, con recarga automática:

```powershell
cd backend
.venv\Scripts\python.exe -m uvicorn app.main:app --env-file .env --host 127.0.0.1 --port 8000 --reload --no-access-log
```

Frontend en otra terminal:

```powershell
cd frontend
npm run dev
```

Abrir `http://127.0.0.1:5173`.

## Comprobación rápida

```powershell
curl http://127.0.0.1:8000/api/health
```

La aplicación no usa base de datos ni guarda los MSG. El archivo original se
mantiene en el navegador y el backend usa temporales efímeros.

## Linux

En Linux se usan los equivalentes `.venv/bin/python` y `python3 -m venv`.


