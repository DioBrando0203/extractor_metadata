# Bloqueos y prevenciones

| Fecha/hora (Lima) | Sintoma | Causa | Prevencion |
|---|---|---|---|
| 2026-10-05 17:57 | Un adjunto defectuoso ocultaba el correo | Parser estricto | Mantener lectura parcial y conservar el resto legible. |
| 2026-10-05 19:27 | MSG con FAT truncada se rechazaba | Cabecera incompleta aunque existian streams | Recuperar solo una copia temporal verificable; no declarar reparacion fisica. |
| 2026-10-05 20:07 | El usuario veia avisos internos sin poder bajar archivos | La interfaz exponia diagnostico pero la API no devolvia binarios | Priorizar correo y descarga; el binario se extrae bajo demanda y se elimina despues. |
| Pendiente | DWG profundo | Formato propietario | Evaluar herramienta y licencia antes de ampliar alcance. |
| Pendiente | Corte abrupto deja temporales | El SO no ejecuta limpieza tras apagado forzado | No prometer borrado garantizado fuera del proceso normal. |
