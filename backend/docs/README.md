# Documentación del backend

Fuente de verdad del servicio local que lee MSG. Metodología: desarrollo guiado por especificaciones (SDD), igual que el frontend. Ningún cambio de comportamiento entra sin spec; ninguna spec queda sin prueba.

## Orden de lectura para una IA o persona nueva

1. `GUIA_IA.md`: protocolo, definición de terminado y prohibiciones. Obligatorio.
2. `ARQUITECTURA.md`: capas, paquetes, dependencias permitidas, flujo y contrato.
3. La spec afectada en `specs/`.
4. `reglas_programacion/REGLAS.md` (PY-xx) y `patrones/PATRONES.md` antes de escribir código.
5. `bloqueos/BLOQUEOS.md` antes de diagnosticar un fallo.

## Mapa

- `GUIA_IA.md`: protocolo para agentes IA.
- `ARQUITECTURA.md`: estructura y límites entre módulos.
- `REQUERIMIENTOS.md`: alcance, cobertura por formato, límites honestos y backlog priorizado (PEN-xx) con su estado.
- `specs/SPEC-B01-analisis.md`: análisis de un MSG.
- `specs/SPEC-B02-adjuntos.md`: descarga, miniaturas y vista previa grande.
- `decisiones/ADR.md`: decisiones con contexto y consecuencias.
- `reglas_programacion/REGLAS.md`: código limpio, tamaño de módulos, tipado, errores, seguridad.
- `patrones/PATRONES.md`: patrones de diseño en uso, cuándo aplicarlos y antipatrones.
- `reglas_estilos/REGLAS.md`: nombres, formato, docstrings y mensajes.
- `reglas_calidad/REGLAS.md`: pruebas y revisión.
- `estilos/API.md`: convenciones del contrato HTTP y códigos de error.
- `calidad/PLAN_CALIDAD.md`: qué prueba cada archivo de tests.
- `calidad/RESULTADOS.md`: última ejecución verificada.
- `tecnologias/STACK.md`: dependencias y fuentes primarias.
- `bloqueos/BLOQUEOS.md`: problemas conocidos.
- `bitacora/BITACORA.md`: registro de trabajo.

## Formato

Escritos para IA con bajo costo de tokens: listas, `clave: valor`, IDs citables. Sin tablas, separadores ni relleno. Plantilla de spec compartida: `frontend/docs/specs/PLANTILLA.md`.
