"""Validadores estructurales de imágenes sueltas: PNG, JPEG y GIF (los usa ``raw_formats``).

Cada uno recibe el archivo abierto y la posición de la firma y devuelve el tamaño exacto de la
imagen, o ``None`` si no cierra: PNG con el CRC de cada bloque, JPEG con sus segmentos hasta EOI y
una decodificación de prueba, GIF con sus bloques hasta el cierre.
"""

import struct
import zlib
from io import BytesIO
from typing import BinaryIO

from PIL import Image

_CHUNK = 1024 * 1024
#: Un archivo rescatado más grande que esto no se valida (ni se descarga entero en memoria).
MAX_RAW_BYTES = 256 * 1024 * 1024
_MAX_DECODE_PIXELS = 100_000_000
_JPEG_STANDALONE = {0x01, *range(0xD0, 0xD8)}


def png_size(source: BinaryIO, offset: int, file_size: int) -> int | None:
    source.seek(offset + 8)
    first_chunk = True
    while source.tell() + 12 <= file_size:
        chunk_header = source.read(8)
        if len(chunk_header) != 8:
            return None
        chunk_size = struct.unpack(">I", chunk_header[:4])[0]
        chunk_type = chunk_header[4:]
        if source.tell() + chunk_size + 4 > file_size:
            return None
        if first_chunk and (chunk_size != 13 or chunk_type != b"IHDR"):
            return None
        payload = source.read(chunk_size)
        checksum = source.read(4)
        if len(payload) != chunk_size or len(checksum) != 4:
            return None
        if struct.unpack(">I", checksum)[0] != zlib.crc32(chunk_type + payload):
            return None
        if chunk_type == b"IEND":
            return source.tell() - offset if chunk_size == 0 else None
        first_chunk = False
    return None


def jpeg_size(source: BinaryIO, offset: int, file_size: int) -> int | None:
    """Recorre los segmentos hasta EOI y confirma que Pillow decodifica la imagen entera."""
    position = offset + 2
    while position + 2 <= min(file_size, offset + MAX_RAW_BYTES):
        source.seek(position)
        marker = source.read(2)
        if len(marker) != 2 or marker[0] != 0xFF:
            return None
        code = marker[1]
        if code == 0xD9:
            size = position + 2 - offset
            return size if _decodes(source, offset, size) else None
        if code in _JPEG_STANDALONE or code == 0xFF:
            position += 1 if code == 0xFF else 2
            continue
        length_bytes = source.read(2)
        if len(length_bytes) != 2 or (length := struct.unpack(">H", length_bytes)[0]) < 2:
            return None
        position += 2 + length
        if code == 0xDA:
            position = _after_entropy_data(source, position, file_size)
            if position is None:
                return None
    return None


def gif_size(source: BinaryIO, offset: int, file_size: int) -> int | None:
    """Recorre descriptor, tablas de color, imágenes y extensiones hasta el cierre ``;``."""
    source.seek(offset + 10)
    packed = source.read(3)[:1]
    if not packed:
        return None
    if packed[0] & 0x80:
        source.seek(3 * (2 << (packed[0] & 7)), 1)
    while source.tell() < min(file_size, offset + MAX_RAW_BYTES):
        block = source.read(1)
        if block == b";":
            return source.tell() - offset
        if block == b",":
            descriptor = source.read(9)
            if len(descriptor) != 9:
                return None
            if descriptor[8] & 0x80:
                source.seek(3 * (2 << (descriptor[8] & 7)), 1)
            source.seek(1, 1)  # Tamaño mínimo del código LZW.
        elif block == b"!":
            source.seek(1, 1)  # Etiqueta de la extensión.
        else:
            return None
        if not _skip_sub_blocks(source, file_size):
            return None
    return None


def _after_entropy_data(source: BinaryIO, position: int, file_size: int) -> int | None:
    """Posición del primer marcador tras los datos comprimidos (``FF00`` y RST no cortan)."""
    source.seek(position)
    while position < file_size:
        data = source.read(_CHUNK)
        if not data:
            return None
        index = 0
        while (found := data.find(b"\xff", index)) >= 0:
            if found + 1 >= len(data):
                break
            following = data[found + 1]
            if following != 0x00 and not 0xD0 <= following <= 0xD7:
                return position + found
            index = found + 2
        position += max(len(data) - 1, 1)
        source.seek(position)
    return None


def _decodes(source: BinaryIO, offset: int, size: int) -> bool:
    """Decodificación de prueba con lista cerrada (PY-23) y límite de píxeles."""
    if size > MAX_RAW_BYTES:
        return False
    source.seek(offset)
    try:
        with Image.open(BytesIO(source.read(size)), formats=("JPEG",)) as image:
            if image.width * image.height > _MAX_DECODE_PIXELS:
                return False
            image.load()
        return True
    except Exception:
        return False


def _skip_sub_blocks(source: BinaryIO, file_size: int) -> bool:
    while source.tell() < file_size:
        length = source.read(1)
        if not length:
            return False
        if length[0] == 0:
            return True
        source.seek(length[0], 1)
    return False
