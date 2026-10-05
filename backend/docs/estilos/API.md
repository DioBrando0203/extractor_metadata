# Estilo de API

Rutas en minúsculas y sustantivos (`/messages/extract`). JSON con claves `snake_case`, fechas ISO-8601 y tamaños en bytes. Errores HTTP incluyen mensaje seguro y código semántico cuando corresponde. Nunca retornar trazas, rutas temporales, bytes de adjuntos ni datos de otro análisis.
