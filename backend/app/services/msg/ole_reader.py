"""Lectura acotada del contenedor OLE de un MSG sin el parser MSG.

Obtiene propiedades MAPI como texto, nombres y tamaños de adjuntos y la página de códigos. Es la
fuente de datos de respaldo cuando `extract_msg` no puede abrir un correo dañado.
"""

import codecs
import struct
from dataclasses import dataclass, field
from pathlib import Path

import olefile

from app.core.config import settings
from app.core.errors import ExtractionError
from app.models.schemas import MetadataItem
from app.services.msg.text import normalize_content_id

ATTACHMENT_DATA_STREAM = "__substg1.0_37010102"
_ATTACHMENT_NAME_STREAM = "__substg1.0_3707001F"
_CONTENT_ID_STREAMS = ("__substg1.0_3712001F", "__substg1.0_3712001E")
_PROPERTIES_STREAM = "__properties_version1.0"
_PROPERTY_PREFIX = "__substg1.0_"
_CODEPAGE_TAG = 0x3FFD0003
_DEFAULT_ANSI = "cp1252"
MAPI_LABELS = {
    "001A": "Clase de mensaje",
    "0037": "Asunto",
    "007D": "Encabezados de transporte",
    "0C1A": "Nombre del remitente",
    "0C1F": "Correo del remitente",
    "0E02": "CCO",
    "0E03": "CC",
    "0E04": "Destinatarios",
    "1000": "Cuerpo de texto",
    "1035": "Message-ID",
    "3001": "Nombre",
    "3003": "Dirección",
    "3704": "Nombre corto del adjunto",
    "3707": "Nombre del adjunto",
    "370E": "MIME del adjunto",
}


@dataclass(frozen=True)
class OleAttachment:
    """Datos de un adjunto que se leen sin abrir su contenido."""

    name: str
    size: int
    #: Content-ID con el que el cuerpo HTML referencia la imagen (``cid:…``), si existe.
    content_id: str | None = None


@dataclass
class OleMetadata:
    """Lo que se pudo leer del contenedor sin interpretar el mensaje."""

    items: list[MetadataItem] = field(default_factory=list)
    #: Texto de propiedades MAPI de primer nivel por identificador, p. ej. ``"0037"`` (asunto).
    recovered: dict[str, str] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    #: Carpeta OLE del adjunto → nombre, tamaño y Content-ID.
    attachments: dict[str, OleAttachment] = field(default_factory=dict)


def attachment_directories(storage_paths: list[list[str]]) -> list[str]:
    """Carpetas ``__attach…`` en el orden del contenedor; ese orden es el índice de la API."""
    directories: list[str] = []
    for parts in storage_paths:
        if parts and parts[0].startswith("__attach") and parts[0] not in directories:
            directories.append(parts[0])
    return directories


def read_ole_metadata(path: Path) -> OleMetadata:
    """Lee streams acotados, sin devolver binarios; sirve también de recuperación parcial."""
    result = OleMetadata()
    try:
        with olefile.OleFileIO(str(path)) as container:
            streams = container.listdir()
            result.attachments = _attachment_entries(container, streams, result.warnings)
            encoding = _ansi_encoding(container, result.warnings)
            if not any(parts[-1].startswith(_PROPERTY_PREFIX) for parts in streams):
                raise ExtractionError(
                    "El archivo OLE no contiene propiedades de un mensaje MSG.", code="NOT_A_MSG"
                )
            if container.parsing_issues:
                result.warnings.append(
                    "El contenedor OLE presenta inconsistencias; la lectura es parcial."
                )
            for parts in streams[: settings.max_properties]:
                _read_stream_item(container, parts, encoding, result)
            if len(streams) > settings.max_properties:
                result.warnings.append(
                    f"Se muestran las primeras {settings.max_properties} propiedades OLE."
                )
    except ExtractionError:
        raise
    except Exception as error:
        raise ExtractionError(
            "El contenedor MSG está corrupto o incompleto y no se puede leer.",
            code="INVALID_OR_CORRUPT_MSG",
        ) from error
    return result


def _attachment_entries(
    container: olefile.OleFileIO, streams: list[list[str]], warnings: list[str]
) -> dict[str, OleAttachment]:
    entries: dict[str, OleAttachment] = {}
    for parts in streams:
        is_data = len(parts) == 2 and parts[0].startswith("__attach")
        if not is_data or parts[-1] != ATTACHMENT_DATA_STREAM:
            continue
        try:
            directory = parts[0]
            name = _small_text(container, [directory, _ATTACHMENT_NAME_STREAM])
            content_id = next(
                (
                    value
                    for stream in _CONTENT_ID_STREAMS
                    if (value := _small_text(container, [directory, stream]))
                ),
                None,
            )
            entries[directory] = OleAttachment(
                name=name or f"adjunto-{len(entries) + 1}",
                size=container.get_size(parts),
                content_id=normalize_content_id(content_id),
            )
        except Exception:
            warnings.append("Un adjunto tiene estructura OLE incompleta.")
    return entries


def _small_text(container: olefile.OleFileIO, path: list[str]) -> str | None:
    """Texto corto de un stream MAPI (nombres, Content-ID); ``None`` si falta o está vacío."""
    if not container.exists(path):
        return None
    with container.openstream(path) as stream:
        raw = stream.read(1024)
    encoding = "utf-16-le" if path[-1].endswith("001F") else "cp1252"
    return raw.decode(encoding, errors="replace").rstrip("\x00") or None


def _ansi_encoding(container: olefile.OleFileIO, warnings: list[str]) -> str:
    """Página de códigos que el MSG declara para sus propiedades ANSI."""
    if not container.exists(_PROPERTIES_STREAM):
        return _DEFAULT_ANSI
    try:
        raw = container.openstream(_PROPERTIES_STREAM).read(32 + settings.max_properties * 16)
        for offset in range(32, len(raw) - 15, 16):
            if struct.unpack_from("<I", raw, offset)[0] != _CODEPAGE_TAG:
                continue
            codepage = struct.unpack_from("<I", raw, offset + 8)[0]
            try:
                return codecs.lookup(f"cp{codepage}").name
            except LookupError:
                warnings.append("Página de códigos desconocida; recuperación ANSI aproximada.")
                return _DEFAULT_ANSI
    except Exception:
        warnings.append("La página de códigos OLE es ilegible; se recupera texto aproximado.")
    return _DEFAULT_ANSI


def _read_stream_item(
    container: olefile.OleFileIO, parts: list[str], encoding: str, result: OleMetadata
) -> None:
    try:
        name = parts[-1]
        size = container.get_size(parts)
        value = f"Binario o estructura: {size:,} bytes (contenido omitido)"
        if name.startswith(_PROPERTY_PREFIX) and name[-4:] in {"001F", "001E"}:
            value = _read_text_stream(container, parts, size, encoding, result.warnings)
            if len(parts) == 1:
                result.recovered[name[12:16]] = value
        property_id = name[12:16] if name.startswith(_PROPERTY_PREFIX) else ""
        label = MAPI_LABELS.get(property_id, name)
        if len(parts) > 1:
            label = "/".join(parts[:-1]) + "/" + label
        result.items.append(MetadataItem(group="MAPI / OLE", label=label, value=value))
    except Exception:
        result.warnings.append(f"Stream OLE ilegible: {'/'.join(parts)}; se conserva el resto.")


def _read_text_stream(
    container: olefile.OleFileIO, parts: list[str], size: int, encoding: str, warnings: list[str]
) -> str:
    """Decodifica un stream de texto MAPI (001F Unicode, 001E ANSI) sin pasar del límite."""
    unicode_stream = parts[-1].endswith("001F")
    limit = (settings.max_property_chars + 1) * (2 if unicode_stream else 1)
    with container.openstream(parts) as stream:
        data = stream.read(limit)
    value = data.decode("utf-16-le" if unicode_stream else encoding, errors="replace")
    value = value.rstrip("\x00")
    if size > limit:
        value += f" … [truncado; {size:,} bytes]"
        notice = "Propiedades extensas: algunos valores se muestran abreviados."
        if notice not in warnings:
            warnings.append(notice)
    return value
