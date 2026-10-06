"""Localiza la miniatura que el propio programa guardó dentro de un DWG, DXF u Office.

No interpreta el dibujo ni el documento: sólo lee la sección de vista previa documentada.
"""

import zipfile
from io import BytesIO
from pathlib import Path

MAX_EMBEDDED_MEMBER_BYTES = 8 * 1024 * 1024


_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


DWG_IMAGE_SENTINEL = bytes.fromhex("1F256D07D43628289D57CA3F9D44102B")


_DWG_IMAGE_PNG = 6


_DWG_IMAGE_BMP = 2


_OFFICE_THUMBNAILS = ("docProps/thumbnail.jpeg", "docProps/thumbnail.jpg", "docProps/thumbnail.png")


def _uint32(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset : offset + 4], "little")


def _dib_to_bmp(dib: bytes) -> bytes | None:
    """Antepone la cabecera de archivo BMP a un DIB (formato de las miniaturas de AutoCAD)."""
    if len(dib) < 12:
        return None
    header_size = _uint32(dib, 0)
    if header_size not in (12, 40, 52, 56, 108, 124) or header_size > len(dib):
        return None
    if header_size == 12:
        bit_count = int.from_bytes(dib[10:12], "little")
        colors, entry_size, masks = 0, 3, 0
    else:
        bit_count = int.from_bytes(dib[14:16], "little")
        compression = _uint32(dib, 16)
        colors, entry_size = _uint32(dib, 32), 4
        masks = 12 if header_size == 40 and compression == 3 else 0
    if bit_count not in (1, 4, 8, 16, 24, 32):
        return None
    if colors == 0 and bit_count <= 8:
        colors = 1 << bit_count
    pixel_offset = 14 + header_size + masks + colors * entry_size
    if pixel_offset > 14 + len(dib):
        return None
    return (
        b"BM"
        + (14 + len(dib)).to_bytes(4, "little")
        + b"\0\0\0\0"
        + pixel_offset.to_bytes(4, "little")
        + dib
    )


def _dwg_thumbnail(payload: bytes) -> bytes | None:
    """Lee la sección de imagen de vista previa que AutoCAD guarda desde R13 (dirección en 0x0D)."""
    if len(payload) < 0x11 or payload[:2] != b"AC" or not payload[2:6].isdigit():
        return None
    address = _uint32(payload, 0x0D)
    records_start = address + len(DWG_IMAGE_SENTINEL) + 5
    if address <= 0 or records_start > len(payload):
        return None
    if payload[address : address + len(DWG_IMAGE_SENTINEL)] != DWG_IMAGE_SENTINEL:
        return None
    count = payload[address + len(DWG_IMAGE_SENTINEL) + 4]
    bitmap: bytes | None = None
    for index in range(min(count, 8)):
        record = payload[records_start + index * 9 : records_start + index * 9 + 9]
        if len(record) < 9:
            break
        code, start, size = record[0], _uint32(record, 1), _uint32(record, 5)
        if size <= 0 or start + size > len(payload):
            continue
        data = payload[start : start + size]
        if code == _DWG_IMAGE_PNG and data.startswith(_PNG_SIGNATURE):
            return data
        if code == _DWG_IMAGE_BMP and bitmap is None:
            bitmap = _dib_to_bmp(data)
    return bitmap


def _dxf_thumbnail(payload: bytes) -> bytes | None:
    """Reconstruye la sección THUMBNAILIMAGE de un DXF ASCII (DIB en hexadecimal, código 310)."""
    marker = payload.find(b"THUMBNAILIMAGE")
    if marker < 0:
        return None
    lines = payload[marker:].decode("latin-1", errors="ignore").splitlines()[1:]
    chunks: list[str] = []
    for code, value in zip(lines[0::2], lines[1::2], strict=False):
        code, value = code.strip(), value.strip()
        if code == "0":
            break
        if code == "310":
            chunks.append(value)
    if not chunks:
        return None
    try:
        return _dib_to_bmp(bytes.fromhex("".join(chunks)))
    except ValueError:
        return None


def _office_thumbnail(payload: bytes) -> bytes | None:
    """Toma `docProps/thumbnail.*`, la portada que Office guarda al activar la vista previa."""
    try:
        with zipfile.ZipFile(BytesIO(payload)) as archive:
            for name in _OFFICE_THUMBNAILS:
                try:
                    info = archive.getinfo(name)
                except KeyError:
                    continue
                if info.file_size > MAX_EMBEDDED_MEMBER_BYTES:
                    return None
                return archive.read(info)
    except (OSError, zipfile.BadZipFile, RuntimeError, ValueError):
        return None
    return None


def embedded_thumbnail(payload: bytes, filename: str) -> bytes | None:
    """Miniatura guardada dentro de un archivo de diseño u Office, si existe."""
    extension = Path(filename).suffix.lower()
    if payload[:2] == b"AC" and payload[2:6].isdigit():
        return _dwg_thumbnail(payload)
    if extension == ".dxf":
        return _dxf_thumbnail(payload)
    if payload.startswith(b"PK\x03\x04"):
        return _office_thumbnail(payload)
    return None
