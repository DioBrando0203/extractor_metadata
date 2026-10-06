# Documentación del frontend

Fuente de verdad del frontend de Inspector MSG. Metodología: desarrollo guiado por especificaciones (SDD). Ningún cambio de comportamiento entra sin spec; ninguna spec queda sin pruebas que la verifiquen.

## Orden de lectura para una IA o persona nueva

1. `GUIA_IA.md`: protocolo de trabajo, definición de terminado y prohibiciones. Obligatorio.
2. `ARQUITECTURA.md`: módulos, dependencias permitidas, flujo de datos y estado.
3. La spec del área afectada en `specs/`.
4. Las reglas que aplican: `reglas_programacion/`, `reglas_estilos/`, `reglas_calidad/`.
5. `estilos/SISTEMA_VISUAL.md` si el cambio toca interfaz.
6. `bloqueos/BLOQUEOS.md` antes de diagnosticar un fallo: puede estar ya resuelto.

Leer sólo lo que el cambio necesita. Cada documento es autosuficiente.

## Mapa

- `GUIA_IA.md`: protocolo para agentes IA.
- `ARQUITECTURA.md`: estructura y límites entre módulos.
- `specs/SPEC-01-layout.md`: estructura de pantalla, navegación, responsive y vista Ayuda.
- `specs/SPEC-02-ingesta.md`: portada, apertura, arrastre, cola y bandeja.
- `specs/SPEC-03-lector.md`: panel de lectura del correo.
- `specs/SPEC-04-adjuntos.md`: lista y descarga de adjuntos.
- `specs/PLANTILLA.md`: plantilla para specs nuevas.
- `decisiones/ADR.md`: decisiones de arquitectura y diseño con su motivo.
- `estilos/SISTEMA_VISUAL.md`: tokens, escalas, anatomía de componentes y breakpoints.
- `reglas_programacion/REGLAS.md`: reglas P-xx de código.
- `reglas_estilos/REGLAS.md`: reglas E-xx de CSS y diseño.
- `reglas_calidad/REGLAS.md`: reglas C-xx de pruebas, accesibilidad y revisión.
- `calidad/PLAN_CALIDAD.md`: qué prueba cada capa y cómo revisar visualmente.
- `calidad/RESULTADOS.md`: última ejecución verificada.
- `tecnologias/STACK.md`: dependencias, versiones y restricciones.
- `bloqueos/BLOQUEOS.md`: problemas conocidos con causa y prevención.
- `bitacora/BITACORA.md`: registro cronológico de trabajo.

## Formato de estos documentos

Escritos para ser leídos por IA con bajo costo de tokens: listas cortas, `clave: valor`, identificadores citables (P-01, CA-03, ADR-02). Sin tablas, sin separadores horizontales, sin adornos. Ver `GUIA_IA.md`, sección Documentación.
