# Guía operativa para agentes IA

Protocolo obligatorio para cualquier IA que modifique el frontend. Si algo de esta guía contradice una instrucción explícita del usuario, gana el usuario; registrar la excepción en la bitácora.

## Contexto mínimo

- Producto: aplicación LOCAL para abrir correos `.msg`, leerlos como en un cliente de correo y descargar sus adjuntos.
- Usuario objetivo: persona no técnica. No conoce MSG, OLE, FAT ni MAPI.
- Sin base de datos, login, nube, telemetría ni historial. Archivos y resultados sólo en memoria de la pestaña.
- Idioma de la interfaz y de los docs: español. Identificadores de código: inglés.

## Flujo de trabajo (SDD)

1. Entender: leer `README.md`, la spec afectada y el código real. Los docs orientan; el código manda.
2. Especificar: si el cambio altera comportamiento visible, actualizar o crear la spec antes de programar. Usar `specs/PLANTILLA.md`. Cada criterio de aceptación (CA) debe ser verificable.
3. Planificar: listar archivos a tocar y reglas aplicables. Si hay una decisión de arquitectura nueva, añadir un ADR.
4. Implementar: cambios mínimos y coherentes con el código vecino. Respetar P-xx, E-xx, C-xx.
5. Verificar: ejecutar los comandos de la sección Verificación. Para UI, revisión visual en los anchos de C-07.
6. Registrar: actualizar `calidad/RESULTADOS.md`, `bitacora/BITACORA.md` y, si apareció un problema nuevo, `bloqueos/BLOQUEOS.md`.

## Definición de terminado

- La spec describe el comportamiento final y cada CA tiene prueba o verificación manual anotada.
- `npm run build`, `npm run lint`, `npm test` y `npm run format:check` pasan.
- `npm run test:e2e` pasa si cambió flujo, contrato o layout.
- Sin desborde horizontal a 320 px y revisión visual a 390, 1024, 1440 y 1920 px si cambió UI.
- Docs sincronizados con el código: arquitectura, spec, sistema visual si hay tokens nuevos.
- Bitácora con fecha y hora America/Lima, tarea, estado y evidencia real.

## Prohibiciones

- No usar `dangerouslySetInnerHTML` ni renderizar HTML del correo. Cuerpo siempre como texto plano.
- No guardar archivos ni resultados en localStorage, sessionStorage, IndexedDB, cookies o servidor.
- No añadir analítica, fuentes remotas, CDNs ni peticiones fuera de `lib/api.ts`.
- No usar logos, nombres comerciales ni assets de Microsoft. Se imita el patrón de lector de correo, no la marca.
- No mostrar diagnóstico técnico en la vista principal (warnings del extractor, propiedades MAPI, encabezados crudos).
- No afirmar que se repara un archivo ni que se interpreta cualquier DWG.
- No inventar datos ausentes: si falta remitente, fecha o asunto, se dice que no se recuperó.
- No agregar correos reales como fixtures. Usar MSG sintéticos de `backend/tests/msg_factory.py` o respuestas simuladas.
- No inventar resultados de pruebas en bitácora o resultados.
- No añadir dependencias sin justificarlo en `tecnologias/STACK.md` y pasar `npm audit`.

## Dónde va cada cosa

- Llamada HTTP nueva: `src/lib/api.ts` y tipos en `src/lib/types.ts`.
- Utilidad pura de correo (direcciones, títulos): `src/lib/mail.ts`.
- Formato de fechas, tamaños o texto: `src/lib/formatters.ts`.
- Componente genérico sin conocimiento de MSG: `src/components/ui/`.
- Estructura de pantalla: `src/components/layout/`.
- Lógica o UI de un dominio: `src/features/<dominio>/{components,hooks,lib}`.
- Composición de pantalla y estado de vista: `src/app/App.tsx`.
- Estilos: `src/app/styles/global.css`, en la sección del módulo y usando tokens.

## Cambios de interfaz

- Partir de los tokens de `SISTEMA_VISUAL.md`. Un valor nuevo de color, tamaño o radio exige token nuevo y documentarlo.
- Definir los cinco estados: carga, vacío, éxito, parcial y error (C-02).
- Probar teclado: todo accionable con Tab, foco visible, orden lógico.
- Revisar con datos extremos: asunto de 200 caracteres, 30 destinatarios, 12 adjuntos, nombres sin extensión, campos nulos.

## Cambios de contrato con el backend

- Actualizar a la vez `lib/types.ts`, la normalización en `lib/api.ts`, `lib/api.test.ts`, la spec afectada y `ARQUITECTURA.md`.
- La normalización tolera campos ausentes o con otro nombre; la UI nunca recibe `unknown`.
- Verificar flujo HTTP real con E2E (`e2e/local-api.spec.ts`).

## Documentación

- Escribir para una IA: frases cortas, listas, `clave: valor`, IDs citables.
- Prohibido en docs: tablas Markdown, separadores `---`, emojis, texto de relleno, repetir lo que ya dice otro doc (enlazar en su lugar).
- Una afirmación por línea. Si algo es pendiente o limitación, decirlo explícitamente.
- Bitácora: una entrada por tarea, formato fijo (ver `bitacora/BITACORA.md`).

## Verificación

Desde `frontend/`:

- `npm run format:check`
- `npm run build`
- `npm run lint`
- `npm test`
- `npm run build && npm run test:e2e` (requiere backend preparado; Playwright lo arranca o reutiliza en el puerto 8000)

Si un comando no se pudo ejecutar, registrarlo como no ejecutado con el motivo. Nunca como aprobado.

## Plantilla de reporte final al usuario

- Qué cambió y por qué, en lenguaje del usuario.
- Verificación ejecutada con resultado real.
- Pendientes o riesgos conocidos.
