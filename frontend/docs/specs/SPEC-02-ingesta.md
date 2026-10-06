# SPEC-02 Ingesta: portada, apertura, cola, bandeja y búsqueda

Estado: implementada
Código: `src/features/ingestion/`, `src/app/App.tsx`, `src/components/ui/SearchBox.tsx`
Relacionadas: SPEC-01, ADR-04, ADR-06

## Objetivo

Que abrir uno o varios `.msg` sea obvio, tolerante a errores, y que encontrarlos en la bandeja sea tan fácil como en un cliente de correo.

## Portada (sin archivos)

- Insignia de privacidad, título "Lee lo que Outlook no pudo", texto de apoyo.
- Zona de arrastre con icono, "Arrastra tus archivos .msg aquí", separador "o" y "Elegir archivos".
- Tres tarjetas: Local, Adjuntos, Lectura parcial. Todo centrado en el lector.

## Apertura

- Un único input oculto en `App`; lo usan portada, "Abrir MSG" y estados vacíos.
- Soltar archivos en cualquier parte de la ventana los agrega; la portada resalta su zona y, con bandeja, aparece `DropOverlay`.
- Soltar un archivo nunca hace que el navegador lo abra y pierda la sesión.

## Cola

- Validación local de extensión `.msg`; si falla, item en error no reintentable.
- Procesamiento secuencial; un error no detiene los siguientes.
- "Limpiar bandeja" vacía la cola, borra la búsqueda y descarta respuestas tardías.

## Bandeja

- Cabecera del panel: "Bandeja" y contador ("3 de 12" mientras se busca).
- Fila de correo: avatar, remitente en semibold y clip si hay adjuntos; asunto (o nombre de archivo) y fecha compacta; vista previa del texto con chip "Parcial" si aplica.
- Fila pendiente: icono de estado (reloj, spinner o error), nombre del archivo, estado y tamaño o motivo del error; reintentar en la esquina si procede.
- Seleccionada: fondo `--brand-150`, barra de marca de 3 px, `aria-current="true"`.
- Pie: "Los archivos sólo viven en la memoria de esta sesión."

## Búsqueda

- Buscador en la cabecera ("Buscar en la bandeja") cuando hay correos.
- Busca en nombre de archivo, asunto, remitente, destinatarios, texto y nombres de adjuntos.
- Sin distinguir mayúsculas ni tildes; todas las palabras deben aparecer.
- Esc o el botón ✕ borran la búsqueda. Sin resultados: mensaje y "Borrar búsqueda".
- Atajo `/` para enfocar el buscador desde cualquier parte (no mientras se escribe en otro campo); la pista `/` se oculta en pantallas táctiles.
- Cada fila coincidente resalta remitente y asunto en amarillo y su tercera línea muestra el fragmento donde aparece la palabra, o "Adjunto: …" si coincide un adjunto.
- El contador indica "N de M" y se anuncia a lectores de pantalla.

## Estados

- Carga: fila con spinner; lector con esqueleto.
- Vacío: portada.
- Éxito: fila completa.
- Parcial: chip "Parcial".
- Error: fila roja y `ExtractionFailed` con motivo, Reintentar y Abrir otro archivo.

## Criterios de aceptación

- CA-01: un error no impide procesar el siguiente y se puede reintentar. Prueba: `useExtractionQueue.test.tsx`.
- CA-02: limpiar durante una extracción no revive items. Prueba: `useExtractionQueue.test.tsx`.
- CA-03: elegir un MSG desde el input muestra el correo. Prueba: `e2e/local-api.spec.ts`.
- CA-04: la búsqueda ignora tildes y mayúsculas y cubre adjuntos. Prueba: `features/ingestion/lib/search.test.ts`.
- CA-05: soltar archivos sobre la bandeja los agrega sin navegar fuera. Prueba: manual.
- CA-06: un MSG corrupto muestra "No se pudo abrir" con motivo. Prueba: captura `07-error` de `test:visual`.

## Pendientes

- Navegar filas con flechas.
- Cancelar un archivo concreto de la cola.

## Criterios añadidos (2026-10-06)

- CA-07: búsqueda sin tildes con rangos correctos sobre el texto original y fragmentos de contexto. Prueba: `lib/textSearch.test.ts`.
- CA-08: la vista previa explica la coincidencia (texto, adjunto o destinatarios) sin mostrar marcadores internos. Prueba: `features/ingestion/lib/search.test.ts`, `lib/thread.test.ts`.
