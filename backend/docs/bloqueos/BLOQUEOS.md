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
Causa: si el mini stream se pierde, también se pierden los nombres y Content-ID de los adjuntos, y el RTF/HTML del cuerpo puede no ser legible. Si sólo se perdió la ubicación de la MiniFAT, se recuperan (B-16, ADR-B19).
Mitigación: las imágenes se muestran en la lista de adjuntos; no se adivina su posición (RQ-13).

## B-12 Una pasada de emparejamiento bloqueaba a la siguiente

Fecha: 2026-10-06. Estado: resuelto.
Síntoma: una imagen con candidato único por proporción no se ubicaba.
Causa: las pasadas por tamaño exacto y por proporción se calculaban a la vez; una imagen ya emparejada seguía compitiendo.
Solución: calcular cada pasada después de aplicar la anterior.
Prevención: `test_inline_recovery.py::test_unique_aspect_ratio_after_exact_matches`.

## B-14 Bytes del PKCS#7 como cuerpo de un correo cifrado

Fecha: 2026-10-07. Estado: resuelto.
Síntoma: un correo S/MIME cifrado u opaco mostraba caracteres sin sentido como texto.
Causa: extract-msg desenvuelve el `smime.p7m` como si fuera MIME y devuelve sus bytes como cuerpo cuando falta el stream `1000`.
Solución: `ReadContext.signed_body` sólo acepta el stream `1000` en correos opacos o cifrados (ADR-B18).
Prevención: `test_smime.py::test_encrypted_and_opaque_signed_mail_are_reported_and_keep_the_p7m`.

## B-15 El rescate perdía imágenes pequeñas del mini stream

Fecha: 2026-10-06. Estado: resuelto.
Síntoma: con el MSG real del usuario, el rescate ampliado dejó de mostrar 2 PNG de 375 y 318 bytes que antes aparecían.
Causa: el mapa de sectores marcaba entero el mini stream como legible, aunque esos adjuntos habían perdido su entrada de directorio.
Solución: dentro del mini stream sólo cuentan los mini sectores que reclama un stream alcanzable (`sector_map`).
Prevención: `test_raw_recovery.py::test_small_loose_file_inside_the_mini_stream_is_found` y comparar con el MSG real antes de cerrar cambios de rescate (PEN-14).

## B-16 Datos cortos vacíos por la MiniFAT perdida

Fecha: 2026-10-08. Estado: resuelto.
Síntoma: en el MSG real, asunto, remitente, nombres y Content-ID de adjuntos se leían vacíos y el parser fallaba; se creía que el mini stream estaba perdido.
Causa: la cabecera tenía el inicio de la MiniFAT en fin de cadena y la cantidad en 0; olefile no carga la MiniFAT y cada stream pequeño devuelve 0 bytes. La MiniFAT y el mini stream seguían en el archivo, encadenados en la FAT, salvo el último enlace del mini stream (apunta a un sector de la FAT).
Solución: ubicar la única tabla que explica cada stream pequeño y reponerla en la copia (ADR-B19).
Prevención: `test_minifat_recovery.py`. Diagnosticar con la estructura (cabecera, cadenas, defectos de olefile) antes de suponer que un dato se perdió.
