"""Descriptores de cada adjunto leídos del árbol OLE sin abrir su contenido.

Cada carpeta ``__attach…`` declara cómo viaja el adjunto (``PidTagAttachMethod``, 0x3705): con sus
bytes (1), como correo adjunto (5), como objeto OLE (6) o como referencia a una ruta o a la nube
(2, 3, 4, 7). Una referencia no trae bytes: sólo queda su dirección (0x370D o 0x3708).
Este módulo sólo describe; cómo se muestra cada adjunto lo decide ``attachments``.
"""

import struct
from dataclasses import dataclass

import olefile

from app.services.msg.text import normalize_content_id

ATTACHMENT_DATA_STREAM = "__substg1.0_37010102"
#: Carpeta con el correo adjunto (método 5) o el objeto OLE (método 6).
EMBEDDED_STORAGE = "__substg1.0_3701000D"
PROPERTIES_STREAM = "__properties_version1.0"
METHOD_EMBEDDED_MESSAGE = 5
#: Por referencia a una ruta (2, 3, 4) o a un servicio web como OneDrive o SharePoint (7).
REFERENCE_METHODS = frozenset({2, 3, 4, 7})
_ATTACH_METHOD_TAG = 0x37050003
#: Bytes reservados al inicio del stream de propiedades de un adjunto, antes de las entradas.
_PROPERTIES_HEADER = 8
_PROPERTY_ENTRY = 16
_MAX_PROPERTY_ENTRIES = 256
_NAME_STREAMS = tuple(
    f"__substg1.0_{tag}{kind}" for tag in ("3707", "3001", "3704") for kind in ("001F", "001E")
)
_CONTENT_ID_STREAMS = ("__substg1.0_3712001F", "__substg1.0_3712001E")
_REFERENCE_STREAMS = tuple(
    f"__substg1.0_{tag}{kind}" for tag in ("370D", "3708") for kind in ("001F", "001E")
)
_SHORT_TEXT_BYTES = 1024
#: Una URL de SharePoint puede ser larga; una dirección cortada no sirve, así que se descarta.
_REFERENCE_BYTES = 8192


@dataclass(frozen=True)
class OleAttachment:
    """Datos de un adjunto que se leen sin abrir su contenido."""

    name: str
    size: int
    #: Content-ID con el que el cuerpo HTML referencia la imagen (``cid:…``), si existe.
    content_id: str | None = None
    #: ``PidTagAttachMethod``; ``None`` si la propiedad falta o es ilegible.
    method: int | None = None
    #: Ruta o URL de un adjunto por referencia.
    reference: str | None = None
    has_data: bool = True
    has_storage: bool = False
    #: La carpeta ``EMBEDDED_STORAGE`` tiene su propio stream de propiedades: es un mensaje.
    storage_is_message: bool = False

    @property
    def is_message(self) -> bool:
        """Correo adjunto. Sin método legible decide como extract_msg: carpeta con propiedades."""
        return self.storage_is_message and self.method in (METHOD_EMBEDDED_MESSAGE, None)

    @property
    def is_reference(self) -> bool:
        """Archivo que vive en una ruta o en la nube: el correo sólo guarda su dirección."""
        return not self.has_data and not self.has_storage and self.method in REFERENCE_METHODS


def attachment_directories(storage_paths: list[list[str]]) -> list[str]:
    """Carpetas ``__attach…`` en el orden del contenedor; ese orden es el índice de la API."""
    directories: list[str] = []
    for parts in storage_paths:
        if parts and parts[0].startswith("__attach") and parts[0] not in directories:
            directories.append(parts[0])
    return directories


def read_attachment_entries(
    container: olefile.OleFileIO, streams: list[list[str]], warnings: list[str]
) -> dict[str, OleAttachment]:
    """Carpeta OLE de cada adjunto → su descriptor; un adjunto ilegible no detiene el resto."""
    entries: dict[str, OleAttachment] = {}
    for position, directory in enumerate(attachment_directories(streams), start=1):
        try:
            entries[directory] = _read_entry(container, directory, position)
        except Exception:
            warnings.append("Un adjunto tiene estructura OLE incompleta.")
    return entries


def _read_entry(container: olefile.OleFileIO, directory: str, position: int) -> OleAttachment:
    data = [directory, ATTACHMENT_DATA_STREAM]
    has_data = bool(container.exists(data))
    content_id = _first_text(container, directory, _CONTENT_ID_STREAMS)
    return OleAttachment(
        name=_first_text(container, directory, _NAME_STREAMS) or f"adjunto-{position}",
        size=container.get_size(data) if has_data else 0,
        content_id=normalize_content_id(content_id),
        method=attach_method(container, directory),
        reference=_first_text(container, directory, _REFERENCE_STREAMS, _REFERENCE_BYTES),
        has_data=has_data,
        has_storage=bool(container.exists([directory, EMBEDDED_STORAGE])),
        storage_is_message=bool(container.exists([directory, EMBEDDED_STORAGE, PROPERTIES_STREAM])),
    )


def attach_method(container: olefile.OleFileIO, directory: str) -> int | None:
    """``PidTagAttachMethod`` del stream de propiedades del adjunto; ``None`` si es ilegible."""
    path = [directory, PROPERTIES_STREAM]
    try:
        if not container.exists(path):
            return None
        with container.openstream(path) as stream:
            raw = stream.read(_PROPERTIES_HEADER + _PROPERTY_ENTRY * _MAX_PROPERTY_ENTRIES)
    except Exception:
        return None
    for offset in range(_PROPERTIES_HEADER, len(raw) - _PROPERTY_ENTRY + 1, _PROPERTY_ENTRY):
        if struct.unpack_from("<I", raw, offset)[0] == _ATTACH_METHOD_TAG:
            return struct.unpack_from("<I", raw, offset + 8)[0]
    return None


def _first_text(
    container: olefile.OleFileIO,
    directory: str,
    streams: tuple[str, ...],
    limit: int = _SHORT_TEXT_BYTES,
) -> str | None:
    """Primer texto MAPI no vacío entre ``streams``; uno más largo que ``limit`` se ignora."""
    for stream in streams:
        path = [directory, stream]
        if not container.exists(path) or container.get_size(path) > limit:
            continue
        with container.openstream(path) as source:
            raw = source.read(limit)
        encoding = "utf-16-le" if stream.endswith("001F") else "cp1252"
        if value := raw.decode(encoding, errors="replace").rstrip("\x00").strip():
            return value
    return None
