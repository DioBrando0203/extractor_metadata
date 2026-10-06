# Reglas de calidad

## Especificación

- C-01: cambio de comportamiento visible implica spec actualizada con criterios de aceptación y su prueba asociada.
- C-02: todo componente que muestre datos remotos define cinco estados: carga, vacío, éxito, parcial y error. Si alguno no aplica, la spec lo dice.

## Pruebas

- C-03: lógica pura (`lib/`, `features/*/lib`) con pruebas unitarias de casos normales, bordes y datos ausentes.
- C-04: componentes de feature con pruebas de React Testing Library por rol y nombre accesible, no por clases CSS.
- C-05: flujos que cruzan frontend y backend con Playwright contra el servicio local real (`e2e/local-api.spec.ts`).
- C-06: fixtures sólo sintéticos: `backend/tests/msg_factory.py` o respuestas simuladas. Nunca correos reales.

## Revisión visual

- C-07: cambios de UI se revisan en 320, 390, 1024, 1440 y 1920 px, con datos extremos (asunto largo, sin remitente, 12 adjuntos, 30 destinatarios).
- C-08: comprobar que `document.documentElement.scrollWidth` no supera `clientWidth` en esos anchos.
- C-09: revisar teclado: Tab recorre en orden lógico, foco visible, Enter y Espacio activan.

## Integración

- C-10: antes de integrar pasan `format:check`, `build`, `lint`, `test` y, si cambió flujo o layout, `test:e2e`.
- C-11: `calidad/RESULTADOS.md` y la bitácora reflejan sólo ejecuciones reales, con fecha America/Lima.
- C-12: un bug corregido deja una prueba que habría fallado antes, o una entrada en bloqueos explicando por qué no es automatizable.
