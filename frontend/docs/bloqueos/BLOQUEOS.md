# Bloqueos y problemas conocidos

Formato por entrada: ID, fecha Lima, síntoma, causa, solución, prevención, estado. Leer antes de diagnosticar un fallo.

## B-01 Backend no disponible

Fecha: 2026-10-05. Estado: mitigado.
Síntoma: "No se pudo conectar con el extractor local" al abrir un MSG.
Causa: servicio en el puerto 8000 apagado o en otro puerto.
Solución: iniciar con `py iniciar.py` (Windows) o `python3 iniciar.py` y confirmar `http://127.0.0.1:8000/api/health`.
Prevención: `lib/api.ts` traduce el fallo de red a un mensaje accionable; Playwright arranca el backend si falta.

## B-02 HTML de correo inseguro

Fecha: 2026-10-05. Estado: resuelto por diseño.
Síntoma: riesgo de scripts, rastreadores o recursos remotos al mostrar el cuerpo.
Causa: los correos suelen traer cuerpo HTML.
Solución: el backend convierte a texto y el frontend lo muestra en `<pre>` (ADR-07).
Prevención: P-05; revisión con búsqueda de `dangerouslySetInnerHTML` (PLAN_CALIDAD).

## B-03 Diagnóstico técnico confunde al usuario

Fecha: 2026-10-05. Estado: resuelto.
Síntoma: avisos sobre FAT, OLE o propiedades MAPI en la vista principal.
Causa: la primera versión mostraba warnings y metadatos crudos.
Solución: se retiran de la vista; sólo una barra neutra de "Lectura parcial".
Prevención: CA-06 de SPEC-03 y aserciones en unitarias y E2E.

## B-04 Playwright sin navegador

Fecha: 2026-10-05. Estado: mitigado.
Síntoma: E2E falla con "Executable doesn't exist".
Solución: `npx playwright install chromium`.

## B-05 Pantalla estirada y desborde en la bandeja

Fecha: 2026-10-05. Estado: resuelto.
Síntoma: la página crecía con el contenido, la bandeja mostraba scroll horizontal y el lector tenía grandes huecos.
Causa: ítems de grid con `min-width: auto` y layout a `min-height: 100vh` sin scroll por panel.
Solución: shell a `100dvh`, columnas `minmax(0, 1fr)`, scroll por panel y tarjeta de lectura con ancho máximo (ADR-01).
Prevención: E-08 a E-11; `test:visual` falla si hay desborde.

## B-06 Soltar un archivo fuera de la zona cerraba la sesión

Fecha: 2026-10-05. Estado: resuelto.
Síntoma: al soltar un MSG fuera de la portada, el navegador abría el archivo y se perdía la bandeja.
Causa: sin `preventDefault` en `dragover`/`drop` a nivel de ventana.
Solución: `useWindowFileDrop` (ADR-06).
Prevención: CA-05 de SPEC-02 (manual).

## B-07 Capturas sin estilos en revisión visual

Fecha: 2026-10-05. Estado: entendido, no es defecto de la app.
Síntoma: una captura de Playwright salió sin CSS.
Causa: el script de revisión dejaba peticiones simuladas colgadas largo tiempo en páginas previas y saturó conexiones del navegador.
Solución: en `e2e/visual.spec.ts` la petición "lenta" no se responde y cada prueba usa su propia página.
Prevención: no simular demoras con `setTimeout` largos en rutas interceptadas.

## B-08 Espacio no separable literal en código

Fecha: 2026-10-05. Estado: resuelto.
Síntoma: ESLint `no-irregular-whitespace` en `formatters.ts`.
Causa: un NBSP literal dentro de una expresión regular.
Solución: usar el escape ` `.
Prevención: escribir siempre caracteres invisibles como escapes.
