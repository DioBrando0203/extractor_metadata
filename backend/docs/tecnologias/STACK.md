# Tecnologías elegidas

Python 3.11+ y FastAPI permiten distribución local Linux/Windows con API tipada y OpenAPI.
extract-msg 0.56 + olefile: parser MSG y recuperación de streams CFB/OLE.
Pillow: dimensiones/EXIF sin decodificar píxeles; pypdf: páginas y propiedades PDF.
ZIP/XML estándar: OOXML sin leer hojas completas. ezdxf: cabecera/unidades/capas DXF.
ExifTool opcional instalado en PATH: metadata adicional de los formatos oficialmente soportados.
Multiprocessing spawn: aislamiento compatible entre plataformas; resource sólo Linux.
pytest/Ruff/httpx: pruebas y análisis estático. openpyxl/python-docx sólo generan fixtures en dev.
Versiones verificadas fijadas en `backend/requirements.lock`; pyproject declara rangos de compatibilidad.

Se sustituyó PyMuPDF por pypdf para la lectura de metadata requerida (sin motor de renderizado).
No hay ORM, BD, cookies, sesiones de usuario, almacenamiento cloud ni telemetría configurada.

Fuentes primarias consultadas:
- [Formato MSG Microsoft](https://learn.microsoft.com/en-us/openspecs/exchange_server_protocols/ms-oxmsg/b046868c-9fbf-41ae-9ffb-8de2bd4eec82)
- [extract-msg](https://msg-extractor.readthedocs.io/en/latest/)
- [olefile](https://olefile.readthedocs.io/en/latest/Howto.html)
- [ExifTool y lista oficial de formatos](https://exiftool.org/)
- [ezdxf](https://ezdxf.readthedocs.io/)
