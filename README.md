# Lector local de correos MSG

Elija o arrastre un archivo `.msg` para leer el correo y descargar los archivos adjuntos que aun se puedan abrir. La aplicacion esta pensada para personas que solo quieren ver su correo: la pantalla se parece a Outlook (bandeja, panel de lectura y buscador), muestra de frente imagenes, PDF y miniaturas de planos AutoCAD, y deja los detalles tecnicos de cada adjunto en el panel Detalles del visor.

Ademas de un correo comun, abre:

- Correos reenviados como adjunto (`.msg` o `.eml`), que se leen como un correo propio con un boton "Volver".
- Adjuntos que viven en OneDrive, SharePoint o una carpeta compartida: se muestran como enlace porque no viajan dentro del correo.
- Reuniones, citas, contactos y tareas, con una tarjeta de cuando, donde y quienes.
- Correos firmados (muestra su contenido y avisa que la firma no se comprueba), cifrados o con permisos (explica por que no se pueden leer).
- Correos danados: recupera lo que sigue entero, incluidas imagenes, PDF y documentos Office sueltos, y lee archivos con la cabecera borrada.
- "Descargar todo" baja un ZIP con los adjuntos; las direcciones web del texto se pueden abrir.

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

## Acceso desde otras PCs de la red (opcional)

Por defecto solo responde en este equipo. Para usarlo como servidor de la red (ADR-B12):

1. Cree `backend/.env` a partir de `backend/.env.example` con la IP de la PC servidor, por ejemplo
   `APP_ALLOWED_HOSTS=localhost,127.0.0.1,[::1],192.168.1.20` y
   `APP_ALLOWED_ORIGINS=http://192.168.1.20:8000,http://127.0.0.1:8000`.
2. Compile la interfaz (`npm run build` en `frontend`) y levante el backend, que la sirve en el mismo puerto:
   `.venv/Scripts/python.exe -m uvicorn app.main:app --env-file .env --host 0.0.0.0 --port 8000 --no-access-log`
   (en Linux, `.venv/bin/python`).
3. Desde las otras PCs abra `http://IP_DEL_SERVIDOR:8000`. Si no abre, permita la entrada al puerto 8000 en el firewall.

Alternativa con Vite: configure `frontend/.env.local` con `VITE_API_URL=http://IP_DEL_SERVIDOR:8000/api`,
agregue `http://IP_DEL_SERVIDOR:5173` a `APP_ALLOWED_ORIGINS` y levante `npm run dev -- --host 0.0.0.0`.

Tras actualizar el codigo (`git pull`), vuelva a compilar la interfaz y reinicie el backend: un servidor en marcha no carga cambios.

## Correos de prueba

Para ver cada funcion sin usar correos reales, genere MSG sinteticos (no se versionan):

```powershell
cd backend
.venv/Scripts/python.exe tests/generar_ejemplos.py ../../msg_de_prueba
```

Crea ocho archivos: correo adjunto y enlace a la nube, reunion, firmado, cifrado, varios adjuntos (Descargar todo), EML adjunto, cabecera danada y enlaces en el texto.

## Cobertura y limites

- Adjuntos legibles se pueden descargar, incluidos imagenes, PDF, Word, Excel y otros formatos cuyos bytes sigan disponibles.
- No existe un limite fijo por peso para el MSG o sus adjuntos; archivos grandes pueden tardar mas.
- Si una parte esta danada, se muestra lo que siga legible. No se afirma reparar el archivo original ni recuperar datos ya perdidos.
- Las firmas digitales no se verifican; un correo cifrado o firmado en formato opaco no se puede leer aqui.
- El cuerpo se muestra como texto: no se ejecutan macros, HTML ni scripts. DWG tiene reconocimiento basico, no interpretacion profunda.
- Estado: cerrado momentaneamente desde el 2026-10-08; lo principal esta cumplido.
- Pendientes y limites al dia: [requerimientos](backend/docs/REQUERIMIENTOS.md).

## Verificacion

```powershell
cd backend
.venv/Scripts/python.exe -m pytest
.venv/Scripts/python.exe -m ruff check app tests
.venv/Scripts/python.exe -m ruff format --check app tests

cd ../frontend
npm run format:check
npm run build
npm run lint
npm test
npm run test:e2e
npm run test:visual
```

Documentacion de continuidad: [guia de agentes](AGENTS.md), [backend](backend/docs/ARQUITECTURA.md), [frontend](frontend/docs/ARQUITECTURA.md) y [requerimientos](backend/docs/REQUERIMIENTOS.md).
