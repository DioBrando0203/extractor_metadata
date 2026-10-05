# Plan de calidad

Usar fixtures sintéticos propios, nunca correos privados. Ejecutar tests, Ruff y chequeo de formato.
Verificar MSG válido/CFB genérico/corrupto, recuperación, cuerpo largo, adjunto >10 MB, ruta Windows,
error por tamaño/origen, timeout, limpieza del temporal y lectura por formato.
Validar contrato real desde navegador junto a build/lint/tests frontend.

Cambiar límites o worker exige volver a ejecutar corpus grande y prueba de timeout.
Cambiar extractor exige documento real sintético del formato y prueba de degradación corrupta.
No confundir test Linux con validación Windows. Resultados y entorno en RESULTADOS.md.
