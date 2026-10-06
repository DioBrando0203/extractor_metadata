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
