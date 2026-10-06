# Reglas de estilo (Python)

- ES-01: identificadores en inglés; mensajes al usuario, docstrings y comentarios en español.
- ES-02: Ruff es la autoridad: líneas de 100 caracteres, imports ordenados (`I`), modernización (`UP`) y bugbear (`B`).
- ES-03: nombres por intención: verbos para funciones (`read_ole_metadata`), sustantivos para datos (`OleMetadata`), `is_`/`has_` para booleanos.
- ES-04: constantes en MAYÚSCULAS al inicio del módulo; privadas con `_`.
- ES-05: orden dentro de un módulo: docstring, imports, constantes, tipos, función pública principal, funciones privadas en orden de uso.
- ES-06: mensajes de error con causa y acción posible: "El análisis excedió 90 segundos. Compruebe que el archivo esté completo e inténtelo de nuevo."
- ES-07: advertencias en lenguaje del usuario cuando lleguen a la interfaz; detalles técnicos sólo en metadatos o códigos.
- ES-08: sin código comentado ni `print`; sin TODO sin registrar en bloqueos o pendientes.
