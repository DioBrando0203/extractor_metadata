# Requerimientos y cobertura

## Prioridad de uso

La aplicacion esta pensada primero para una persona que no conoce formatos MSG, OLE, FAT ni metadata. Debe poder elegir un correo, leer su asunto, remitente, contenido y descargar los archivos que encuentre. Los detalles de diagnostico permanecen internos y no son parte de la vista principal.

## Criterios verificables

| Requisito | Cobertura actual |
|---|---|
| Aplicacion local | Loopback, sin cuenta, base de datos, nube, telemetria ni historial. |
| Privacidad | Estado en memoria del navegador; temporales efimeros del backend. |
| Original intacto | Solo se analiza una copia temporal; no se escribe sobre el MSG elegido. |
| Correo legible | Asunto, remitente, destinatarios, fecha y cuerpo de texto cuando los streams existen. |
| Adjuntos descargables | Cada adjunto legible se entrega bajo demanda como descarga temporal, incluidos imagenes, PDF, Word y Excel. |
| Sin limite fijo de peso | MSG y adjuntos se copian/procesan por bloques; el timeout aumenta con el tamano. |
| Lectura parcial | Si una parte esta danada, se conserva lo que siga legible; PNG/PDF completos fuera de enlaces OLE se validan y se ofrecen como recuperados, sin afirmar reparar el archivo. |
| Formatos | Imagenes, PDF, Office OOXML, DXF y firma basica DWG; otros conservan nombre y bytes si el stream es legible. |
| Seguridad | Sin macros ni HTML activo; host y Origin externos rechazados. |
| Pruebas | MSG y adjuntos sinteticos; nunca se agrega un correo privado al repositorio. |

## Limites honestos

No es posible recuperar datos que ya no estan presentes en el archivo. Un adjunto puede mostrarse y descargarse aunque no sea posible obtener todos sus detalles. DWG solo tiene reconocimiento basico; no se promete interpretacion profunda. Un corte de energia o terminacion forzada puede impedir la limpieza normal de temporales del sistema.

## Pendientes fuera del alcance actual

- Adjuntos MSG anidados y objetos OLE embebidos.
- Lectura profunda de DWG con una herramienta evaluada y licenciada.
- Corpus autorizado de corrupciones reales, sin incorporar correos privados.
- Empaquetado instalable para Windows.
