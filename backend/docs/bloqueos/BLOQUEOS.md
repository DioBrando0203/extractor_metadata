# Bloqueos y problemas conocidos (backend)

Formato: ID, fecha Lima, síntoma, causa, solución o prevención, estado.

## B-01 Un adjunto defectuoso ocultaba el correo

Fecha: 2026-10-05 17:57. Estado: resuelto.
Causa: parser estricto.
Prevención: tolerancia por elemento (PY-17); lectura parcial conserva el resto.

## B-02 MSG con FAT truncada se rechazaba

Fecha: 2026-10-05 19:27. Estado: resuelto.
Causa: cabecera con menos FAT declaradas que las enlazadas.
Prevención: reparar sólo una copia temporal verificable (ADR-B03); no declarar reparación física.

## B-03 El usuario veía avisos internos sin poder bajar archivos

Fecha: 2026-10-05 20:07. Estado: resuelto.
Causa: la API no entregaba binarios.
Prevención: descarga bajo demanda con borrado del temporal (SPEC-B02).

## B-04 Los adjuntos sólo mostraban un icono

Fecha: 2026-10-05. Estado: resuelto.
Causa: la respuesta no incluía imagen alguna del adjunto.
Solución: miniaturas en la respuesta y vista previa grande (ADR-B05).

## B-05 DWG profundo

Estado: pendiente.
Causa: formato propietario; render exige herramienta con licencia.
Mitigación: miniatura incrustada y versión de formato (ADR-B08).

## B-06 Corte abrupto deja temporales

Estado: límite honesto.
Causa: el sistema no ejecuta `finally` tras un apagado forzado.
Prevención: no prometer borrado garantizado fuera del proceso normal.

## B-07 EMF/WMF sin miniatura en Linux

Estado: límite honesto.
Causa: Pillow sólo renderiza WMF/EMF en Windows.
Mitigación: el adjunto se descarga igual; el visor ofrece descarga.

## B-08 Módulos de más de 600 líneas

Fecha: 2026-10-05. Estado: resuelto.
Causa: crecimiento sin división por responsabilidad.
Solución: paquetes `msg/`, `metadata/`, `previews/` (ADR-B07). Prevención: PY-01 y PY-02.

## B-09 El servidor ya iniciado no carga cambios

Fecha: 2026-10-05. Estado: entendido.
Síntoma: E2E o pruebas manuales usan código viejo.
Causa: `iniciar.py` arranca Uvicorn sin recarga y Playwright reutiliza el servidor existente.
Prevención: detener el proceso del puerto 8000 antes de verificar cambios del backend.

## B-10 Remitente y asunto perdidos en un MSG con FAT dañada

Fecha: 2026-10-06. Estado: resuelto.
Síntoma: "Mensaje sin asunto" y "Remitente desconocido" aunque el archivo los contenía.
Causa: el parser falla y las propiedades cortas viven en el mini stream, ilegible tras el daño; la recuperación sólo miraba esas propiedades.
Solución: cadena de respaldo con los encabezados de transporte (ADR-B09).
Prevención: CA-10 a CA-12 de SPEC-B01.

## B-11 Posición de imágenes en un MSG muy dañado

Estado: mitigado (ADR-B11); límite honesto para los casos ambiguos.
Causa: si el mini stream se pierde, también se pierden los nombres y Content-ID de los adjuntos, y el RTF/HTML del cuerpo puede no ser legible.
Mitigación: las imágenes se muestran en la lista de adjuntos; no se adivina su posición (RQ-13).

## B-12 Una pasada de emparejamiento bloqueaba a la siguiente

Fecha: 2026-10-06. Estado: resuelto.
Síntoma: una imagen con candidato único por proporción no se ubicaba.
Causa: las pasadas por tamaño exacto y por proporción se calculaban a la vez; una imagen ya emparejada seguía compitiendo.
Solución: calcular cada pasada después de aplicar la anterior.
Prevención: `test_inline_recovery.py::test_unique_aspect_ratio_after_exact_matches`.
