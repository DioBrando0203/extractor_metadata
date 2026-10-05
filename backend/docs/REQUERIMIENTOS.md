# Requisitos originales y evaluación

El requisito principal es un inspector local sencillo de MSG que Outlook/extensiones no logran leer.
Separar frontend y backend, sin login, BD, registro de usuarios ni servidor remoto. Archivos originales
inalterados. Procesar nombres/rutas problemáticas, archivos corruptos y adjuntos de más de 10 MB;
mostrar metadata organizada con estética de lector de correo y mejoras responsive.

## Criterios verificables

| Requisito | Implementación / verificación |
|---|---|
| Local y sin almacenamiento persistente | API loopback, temporales con contexto y borrado, estado React en memoria. |
| Linux y Windows | `pathlib`, `tempfile`, proceso `spawn`, lanzador Python y `.bat`. Windows requiere prueba nativa adicional. |
| Carga arrastrar/elegir múltiples MSG | Cola de frontend por archivo y un endpoint multipart. |
| Vista estilo correo | Remitente, asunto, cuerpo, encabezados, propiedades y adjuntos separados. |
| Nombre/ruta problemáticos | Copia temporal `input.msg`, nombre original sólo presentación, diagnóstico Windows. |
| Corrupción | Validación CFB/OLE, recuperación parcial de texto, errores individuales. |
| Más de 10 MB | Carga 100 MB por MSG, lectura real probada con adjunto sintético 11 MB. |
| Metadata extensa | Texto/propiedades acotados con truncado explícito; binarios fuera del JSON. |
| Imagen/PDF/Office/CAD | Extractores por formato, base genérica para todos, advertencias de cobertura. |
| React modular y componentes compartidos | `features/` + `components/ui` + tokens Tailwind globales. |
| API con framework y rutas separadas | FastAPI, modelos Pydantic, servicios, worker y middleware. |
| Documentación de continuidad | `AGENTS.md`, arquitecturas, reglas y bitácoras en ambos lados. |
| Calidad | Corpus MSG sintético, pruebas extractores/HTTP/frontend y comprobación en navegador. |

## Interpretación de límites

“Cualquier archivo” significa aceptar un adjunto sin bloquear el resto del MSG, obtener propiedades
genéricas y usar un extractor especializado cuando existe. No garantiza recuperar bytes destruidos
ni interpretar formatos propietarios. DWG muestra firma y versión; DXF incluye propiedades con ezdxf.
ExifTool amplía formatos que figuran en su lista oficial; DWG no figura como soporte de lectura.

El navegador no informa la ruta original; una advertencia de nombre no puede diagnosticar esa ruta.
La copia de nombre corto evita trasladar limitaciones de ruta al parser, sin renombrar el original.

La API usa temporales únicamente durante el análisis. El navegador también puede usar su caché o
temporales internos al elegir archivos; la aplicación no crea biblioteca ni historial persistente.
La descarga explícita de un informe es una acción del usuario y crea un archivo donde él elija.

## Pendientes fuera de la cobertura inicial

- Vista/propiedades profundas de DWG con herramienta ODA o equivalente, tras evaluar licencia.
- Expandir adjuntos MSG anidados y objetos OLE de aplicaciones externas.
- Empaquetado instalable para Windows y pruebas nativas Windows.
- Corpus real autorizado de MSG dañados: las pruebas actuales no prueban toda corrupción posible.
