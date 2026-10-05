# Reglas de programación

1. Tipar funciones públicas y serializar respuestas mediante Pydantic.
2. Rutas sólo coordinan HTTP; la extracción vive en servicios o extractores.
3. Nunca formar comandos con entradas del usuario ni usar `shell=True`.
4. Aplicar límites de tamaño, timeout y limpieza con `finally` a todo procesamiento externo.
5. No persistir archivos, metadatos, rutas ni logs con datos personales.
6. Un adjunto fallido debe producir advertencia individual, no perder el mensaje completo.
