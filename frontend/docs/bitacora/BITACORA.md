# Bitácora

Una entrada por tarea, la más reciente al final. Formato fijo:

```text
## AAAA-MM-DD HH:MM -05:00 Título corto
Estado: terminada | parcial | bloqueada
Cambios: qué se tocó (archivos o módulos)
Evidencia: comandos ejecutados y resultado real
Notas: decisiones, ADR o bloqueos relacionados
```

## 2026-10-05 18:10 -05:00 Cola local y lector responsive

Estado: terminada
Cambios: `features/ingestion`, `features/message-viewer`.
Evidencia: no registrada en detalle en su momento.

## 2026-10-05 20:13 -05:00 Vista centrada en leer y descargar

Estado: terminada
Cambios: tres pestañas simples, botón Descargar, retiro de diagnósticos técnicos.
Evidencia: 5 E2E aprobados, incluida descarga real de adjunto sintético.
Notas: Chromium de Playwright instalado (B-04).

## 2026-10-05 21:05 -05:00 Rediseño tipo cliente de correo y documentación SDD

Estado: terminada
Cambios: layout de alto fijo con rail, bandeja y lector (ADR-01); panel de lectura sin pestañas con encabezado, destinatarios, adjuntos y cuerpo (ADR-02); maestro-detalle móvil (ADR-03); arrastre en toda la ventana (ADR-06); tokens y escalas en `global.css` (ADR-08); nuevos `lib/mail.ts`, `features/attachments/lib/fileKind.ts`, `Avatar`, `EmptyState`, `MessageLoading`, `ExtractionFailed`, `DropOverlay`, `HelpPage`; eliminado `MetadataTable` sin uso; favicon en línea; `e2e/visual.spec.ts` y script `test:visual`. Docs reescritos: índice, guía IA, specs SPEC-01 a 04, ADR, sistema visual, reglas P/E/C, plan, stack y bloqueos.
Evidencia: format:check, build y lint aprobados; 28 unitarias; 5 E2E; 5 visuales en 320 a 1920 px sin desborde. Detalle en `calidad/RESULTADOS.md`.
Notas: corregidos B-05 (pantalla estirada y desborde) y B-06 (soltar archivo cerraba la sesión). Pendientes en cada spec.

## 2026-10-06 00:37 -05:00 Estilo Outlook con Fluent 2, miniaturas y visor de adjuntos

Estado: terminada
Cambios: tokens e iconos de Fluent 2 (ADR-09) y retiro de lucide-react; cabecera con buscador, barra de apps, barra de comandos y paneles redondeados; asunto fuera de la tarjeta del mensaje; tarjetas con miniatura y chips de archivo (SPEC-04); visor a pantalla completa con imagen, PDF, texto, vídeo, audio, miniatura incrustada y detalles (SPEC-05, ADR-10, ADR-11); búsqueda en la bandeja (ADR-12); CSS dividido en 13 archivos (ADR-08); componentes y hooks nuevos (`SearchBox`, `Spinner`, `QueueRow`, `RecipientList`, `AttachmentTiles`, `AttachmentViewer`, `AttachmentPreview`, `AttachmentDetails`, `FileTypeIcon`, `useAttachmentFiles`, `viewerMode`, `decodeText`, `search`). Docs: reglas de reutilización y tamaño (P-23 a P-30, E-05), catálogo `patrones/PATRONES.md`, sistema visual, arquitectura, specs y bloqueos B-09 a B-11.
Evidencia: format:check, build, lint y audit aprobados; 39 unitarias; 6 E2E con backend real reiniciado; 5 visuales sin desborde. Detalle en `calidad/RESULTADOS.md`.
Notas: el visor tuvo un fallo de altura corregido tras medirlo (B-09). Las pruebas E2E exigen reiniciar el backend cuando cambia (B-10).
