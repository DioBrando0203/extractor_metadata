# Bloqueos y errores que no deben repetirse

| Fecha/hora (Lima) | Síntoma | Causa | Resolución / prevención |
|---|---|---|---|
| 2026-10-05 17:49 | Entorno incompleto en entrega inicial | Faltaban venv/Node y no se ejecutaron pruebas | Crear venv, instalar deps, cargar nvm; no declarar entrega verificada sólo con compileall. |
| 2026-10-05 17:55 | ExifTool usado como si leyera DWG | Cobertura supuesta sin fuente | DWG no aparece en lista oficial; cabecera nativa y aviso de lectura profunda ausente. |
| 2026-10-05 17:55 | Argumento -FileName= en metadata | Es asignación de etiqueta, no lectura | Sólo argumentos constantes -j -G1 -s - por stdin; test dedicado. |
| 2026-10-05 17:57 | Un adjunto defectuoso podía ocultar todos | Inicialización estricta del parser | errorBehavior tolerante, aviso individual y conservación del mensaje. |
| 2026-10-05 17:57 | Fixture MSG sin streams de nombre | Named properties incompletas | Generador sintético CFB completo con nameid; no atribuir a parser un fixture inválido. |
| 2026-10-05 18:00 | Metadata extensa puede inflar JSON | Valores ilimitados | Valores/budget/cantidad limitados; truncado explícito. |
| Pendiente | DWG profundo | Formato propietario fuera de cobertura libre inicial | Evaluar ODA y licencia si se amplía el alcance. |
| Pendiente | Corte abrupto puede dejar temporal | SO no ejecuta finally tras SIGKILL/apagado | Temporal aislado del SO; no persistencia deliberada ni promesa de borrado tras apagado. |
