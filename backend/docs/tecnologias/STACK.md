# Stack del backend

Rangos en `pyproject.toml`; versiones verificadas en `requirements.lock`.

## Ejecución

- Python 3.11+ y FastAPI: API tipada local con OpenAPI; Uvicorn en 127.0.0.1.
- extract-msg 0.56 y olefile: parser MSG y lectura directa de streams CFB/OLE para recuperación.
- Pillow: metadatos de imagen y miniaturas JPEG con lista cerrada de formatos (ADR-B06).
- pypdf: páginas y propiedades de PDF, sin render (se sustituyó PyMuPDF).
- zipfile y xml.etree estándar: Office Open XML leyendo sólo `docProps`, con límites anti bomba ZIP.
- ezdxf: versión, unidades y capas de DXF.
- ExifTool opcional en PATH: metadatos adicionales, por stdin y con plazo.
- multiprocessing `spawn`: aislamiento igual en Linux y Windows; `resource` sólo en Linux.

## Desarrollo

- pytest, httpx (TestClient) y Ruff.
- openpyxl y python-docx sólo para generar fixtures en pruebas.

## Restricciones

- Sin ORM, base de datos, cookies, sesiones, nube ni telemetría.
- Dependencia nueva: justificar aquí, fijar en `requirements.lock` y probar en Windows y Linux.

## Fuentes primarias

- [Formato MSG (MS-OXMSG)](https://learn.microsoft.com/en-us/openspecs/exchange_server_protocols/ms-oxmsg/b046868c-9fbf-41ae-9ffb-8de2bd4eec82)
- [extract-msg](https://msg-extractor.readthedocs.io/en/latest/)
- [olefile](https://olefile.readthedocs.io/en/latest/Howto.html)
- [ExifTool](https://exiftool.org/)
- [ezdxf](https://ezdxf.readthedocs.io/)
- [Pillow, formatos de archivo](https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html)
- Open Design Alliance, "Open Design Specification for .dwg files", sección de datos de imagen de vista previa (dirección en 0x0D, centinela de 16 bytes, registros código/inicio/tamaño).
