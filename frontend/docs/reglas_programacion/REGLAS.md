# Reglas de programación

1. TypeScript estricto, sin `any` público.
2. Las llamadas HTTP viven en `lib/api.ts`, no en componentes de presentación.
3. Estado de sesión en memoria; no almacenar archivos o resultados en localStorage/IndexedDB.
4. Componentes de feature no importan detalles de otra feature.
5. Nunca renderizar HTML de correo sin sanitización comprobada.
