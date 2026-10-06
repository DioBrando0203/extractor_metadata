# SPEC-02 Ingesta: portada, apertura, cola y bandeja

Estado: implementada
Código: `src/features/ingestion/`, `src/app/App.tsx`
Relacionadas: SPEC-01, ADR-04, ADR-06

## Objetivo

Que abrir uno o varios `.msg` sea obvio, tolerante a errores y que el progreso de cada archivo se vea en una bandeja con aspecto de lista de correo.

## Portada (sin archivos)

- Insignia de privacidad, título "Lee lo que Outlook no pudo", texto de apoyo.
- Zona de arrastre con icono, "Arrastra tus archivos .msg aquí", separador "o" y botón "Elegir archivos".
- Tres tarjetas: Local, Adjuntos, Lectura parcial.
- Centrada vertical y horizontalmente en el lector.

## Apertura

- Un único `<input type=file multiple accept=".msg">` oculto en `App`; lo usan portada, "Abrir MSG" y los estados vacíos.
- Arrastrar archivos sobre cualquier parte de la ventana los agrega. Mientras se arrastra: la portada resalta la zona; con bandeja visible aparece `DropOverlay`.
- Soltar un archivo nunca hace que el navegador lo abra y pierda la sesión.

## Cola

- Validación local: extensión `.msg`. Si falla, item en `error` no reintentable.
- Procesamiento secuencial; un error no detiene los siguientes.
- Reintentar sólo en items con error y extensión válida.
- Limpiar vacía la bandeja, cancela la cola pendiente y descarta resultados que lleguen después.

## Bandeja

- Cabecera: botón primario "Abrir MSG", título "Bandeja", contador y "Limpiar".
- Fila de correo leído: avatar con iniciales, remitente, fecha compacta, asunto (o nombre del archivo), clip si hay adjuntos, vista previa del cuerpo y chip "Parcial" si aplica.
- Fila pendiente: icono de estado, nombre del archivo, estado ("En espera", "Leyendo correo…", "No se pudo leer") y tamaño o error.
- Seleccionada: fondo `--brand-50`, barra izquierda de 3 px y `aria-current="true"`.
- Botón reintentar de 28 px en la esquina inferior derecha de filas con error reintentable.
- Pie: "Los archivos sólo viven en la memoria de esta sesión."

## Estados

- Carga: fila con spinner; lector con esqueleto (SPEC-03).
- Vacío: portada.
- Éxito: fila completa.
- Parcial: fila completa con chip "Parcial".
- Error: fila roja y `ExtractionFailed` en el lector con mensaje del backend, Reintentar y Abrir otro archivo.

## Criterios de aceptación

- CA-01: un error en el primer archivo no impide procesar el segundo y el primero puede reintentarse. Prueba: `useExtractionQueue.test.tsx`.
- CA-02: limpiar durante una extracción no revive items ni selección. Prueba: `useExtractionQueue.test.tsx`.
- CA-03: elegir un MSG desde el input muestra el correo. Prueba: `e2e/local-api.spec.ts`.
- CA-04: un MSG corrupto muestra "No se pudo abrir" con el motivo y los demás continúan. Prueba: manual con respuesta 422.
- CA-05: soltar archivos sobre la bandeja los agrega sin navegar fuera. Prueba: manual.
- CA-06: textos largos de la fila se recortan con elipsis sin desbordar la columna. Prueba: manual a 1024 px.

## Accesibilidad

- Bandeja: `aside` con nombre "Bandeja de correos"; filas como botones; el clip tiene texto oculto ", con adjuntos".
- Estado de carga anunciado con `role="status"` en el lector.

## Pendientes

- Navegación con flechas arriba/abajo entre filas.
- Cancelar un archivo concreto de la cola.
