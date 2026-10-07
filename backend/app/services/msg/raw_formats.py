"""Formatos que se pueden rescatar de datos sueltos: firma, validador estructural y nombre.

Cada validador recibe el archivo abierto y la posición de la firma y devuelve el tamaño exacto del
archivo encontrado, o ``None`` si su estructura no cierra. Sólo se acepta lo que se valida entero:
imágenes en ``raw_images``; aquí, ZIP/Office con el directorio central coherente y PDF hasta su
propio cierre (``startxref`` válido) sin pasar a otro PDF.
"""

import re
import struct
from collections.abc import Callable
from dataclasses import dataclass
from typing import BinaryIO

from app.services.msg.raw_images import MAX_RAW_BYTES, gif_size, jpeg_size, png_size

_CHUNK = 1024 * 1024
_EOCD = b"PK\x05\x06"
_EOCD_SIZE = 22
_PDF_HEADER = b"%PDF-"
_PDF_TRAILER_BYTES = 64
_STARTXREF = re.compile(rb"startxref\s+(\d+)\s*%%EOF$")
_OBJECT = re.compile(rb"\d+\s+\d+\s+obj")

SizeFinder = Callable[[BinaryIO, int, int], int | None]


@dataclass(frozen=True)
class RawFormat:
    signature: bytes
    find_size: SizeFinder
    label: str
    extension: str
    content_type: str


def pdf_size(source: BinaryIO, offset: int, file_size: int) -> int | None:
    """Hasta el último ``%%EOF`` cuyo ``startxref`` apunta a una tabla de este mismo PDF.

    Así se conservan las actualizaciones incrementales sin tragarse otro PDF posterior. Si ningún
    cierre se valida (PDF dañado), se corta en el primero.
    """
    ends = _pdf_eofs(source, offset, min(file_size, offset + MAX_RAW_BYTES))
    valid = [end for end in ends if _xref_belongs(source, offset, end)]
    end = valid[-1] if valid else (ends[0] if ends else None)
    if end is None:
        return None
    source.seek(end)
    following = source.read(2)
    # El fin de línea tras ``%%EOF`` es parte del archivo original.
    newline = 2 if following == b"\r\n" else 1 if following[:1] in (b"\n", b"\r") else 0
    return end + newline - offset


def zip_size(source: BinaryIO, offset: int, file_size: int) -> int | None:
    """Fin del ZIP: el primer EOCD cuyo directorio central empieza donde este ZIP dice."""
    source.seek(offset)
    tail = b""
    position = offset
    while position - offset < MAX_RAW_BYTES and (chunk := source.read(_CHUNK)):
        data = tail + chunk
        search_from = 0
        while (found := data.find(_EOCD, search_from)) >= 0:
            eocd = position - len(tail) + found
            search_from = found + 1
            size = _zip_end(source, offset, eocd, file_size)
            if size is not None:
                return size
            source.seek(position + len(chunk))
        tail = data[-3:]
        position += len(chunk)
    return None


RAW_FORMATS: tuple[RawFormat, ...] = (
    RawFormat(b"\x89PNG\r\n\x1a\n", png_size, "imagen", ".png", "image/png"),
    RawFormat(b"\xff\xd8\xff", jpeg_size, "imagen", ".jpg", "image/jpeg"),
    RawFormat(b"GIF89a", gif_size, "imagen", ".gif", "image/gif"),
    RawFormat(b"GIF87a", gif_size, "imagen", ".gif", "image/gif"),
    RawFormat(b"%PDF-", pdf_size, "documento", ".pdf", "application/pdf"),
    RawFormat(b"PK\x03\x04", zip_size, "archivo", ".zip", "application/zip"),
)


def _zip_end(source: BinaryIO, offset: int, eocd: int, file_size: int) -> int | None:
    source.seek(eocd)
    record = source.read(_EOCD_SIZE)
    if len(record) != _EOCD_SIZE:
        return None
    directory_size, directory_offset, comment = struct.unpack_from("<IIH", record, 12)
    if eocd - directory_size - directory_offset != offset:
        return None
    end = eocd + _EOCD_SIZE + comment
    return end - offset if end <= file_size and directory_size > 0 else None


def _pdf_eofs(source: BinaryIO, offset: int, limit: int) -> list[int]:
    """Posiciones justo después de cada ``%%EOF`` desde ``offset`` y antes del siguiente PDF.

    Un PDF no contiene otra cabecera ``%PDF-`` visible: donde aparece, empieza otro archivo.
    """
    source.seek(offset + len(_PDF_HEADER))
    tail = b""
    position = offset + len(_PDF_HEADER)
    ends: list[int] = []
    while position < limit and (chunk := source.read(min(_CHUNK, limit - position))):
        data = tail + chunk
        base = position - len(tail)
        if (header := data.find(_PDF_HEADER)) >= 0:
            data, limit = data[:header], base + header
        search_from = 0
        while (found := data.find(b"%%EOF", search_from)) >= 0:
            ends.append(base + found + len(b"%%EOF"))
            search_from = found + 1
        tail = data[-4:]
        position += len(chunk)
    return ends


def _xref_belongs(source: BinaryIO, offset: int, end: int) -> bool:
    source.seek(max(offset, end - _PDF_TRAILER_BYTES))
    match = _STARTXREF.search(source.read(end - max(offset, end - _PDF_TRAILER_BYTES)))
    if not match:
        return False
    target = offset + int(match.group(1))
    if not offset <= target < end:
        return False
    source.seek(target)
    head = source.read(32)
    return head.startswith(b"xref") or _OBJECT.match(head) is not None
