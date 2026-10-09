"""Reparación de la cabecera CFB en una copia temporal; el MSG original nunca se modifica.

Tres daños verificables: la firma inicial borrada (con el resto de la cabecera coherente), una DIFAT
truncada cuyas FAT aún se enlazan entre sí y la ubicación de la MiniFAT perdida cuando una única
cadena la explica (``minifat_recovery``). Cualquier otro daño de cabecera no se repara.
"""

import shutil
import struct
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory

from app.services.msg.minifat_recovery import locate_minifat, minifat_lost

CFB_SIGNATURE = bytes.fromhex("D0CF11E0A1B11AE1")


CFB_FREE_SECTOR = 0xFFFFFFFF


CFB_FAT_SECTOR = 0xFFFFFFFD
_HEADER_SIZE = 512
_BYTE_ORDER = 0xFFFE
_MINI_STREAM_CUTOFF = 4096
#: Versión mayor del CFB → desplazamiento de sector que exige (512 o 4096 bytes).
_SECTOR_SHIFT = {3: 9, 4: 12}
_SIGNATURE_NOTICE = (
    "Se reconstruyó la firma del archivo en una copia temporal; el MSG original no fue modificado."
)
_FAT_NOTICE = "Se recuperó la tabla FAT en una copia temporal; el MSG original no fue modificado."
_MINIFAT_NOTICE = (
    "Se recuperó la tabla de datos cortos (MiniFAT: asunto, nombres de adjuntos) en una copia "
    "temporal; el MSG original no fue modificado."
)
#: Inicio y cantidad de sectores de la MiniFAT en la cabecera.
_MINIFAT_FIELDS = 60


def _read_header(path: Path) -> bytes:
    try:
        with path.open("rb") as source:
            return source.read(_HEADER_SIZE)
    except OSError:
        return b""


def header_is_coherent(header: bytes) -> bool:
    """Campos fijos de una cabecera CFB v3/v4, sin mirar la firma."""
    if len(header) != _HEADER_SIZE:
        return False
    major, byte_order, sector_shift, mini_shift = struct.unpack_from("<HHHH", header, 26)
    cutoff = struct.unpack_from("<I", header, 56)[0]
    return (
        _SECTOR_SHIFT.get(major) == sector_shift
        and byte_order == _BYTE_ORDER
        and mini_shift == 6
        and cutoff == _MINI_STREAM_CUTOFF
    )


def signature_lost(header: bytes) -> bool:
    """La firma no está pero el resto de la cabecera es la de un CFB: se puede reponer."""
    return header[:8] != CFB_SIGNATURE and header_is_coherent(header)


def readable_container(path: Path) -> bool:
    """El archivo es un CFB o lo será al reponer su firma en una copia."""
    header = _read_header(path)
    return header[:8] == CFB_SIGNATURE or signature_lost(header)


def recover_fat_sectors(path: Path) -> list[int] | None:
    """Reconstruye una DIFAT truncada cuando sus FAT aún se enlazan entre sí.

    Algunos MSG dañados conservan todos sus streams pero declaran menos FAT de
    los que el propio mapa marca. Sólo se acepta CFB v3/v4 con sectores y
    referencias verificables; el contenido no se altera.
    """
    try:
        with path.open("rb") as source:
            prefix = source.read(_HEADER_SIZE)
            if prefix[:8] != CFB_SIGNATURE and not signature_lost(prefix):
                return None
            if len(prefix) != _HEADER_SIZE:
                return None
            major_version = struct.unpack_from("<H", prefix, 26)[0]
            sector_shift = struct.unpack_from("<H", prefix, 30)[0]
            sector_size = 1 << sector_shift
            if major_version not in {3, 4} or sector_size not in {512, 4096}:
                return None
            file_size = path.stat().st_size
            if file_size <= sector_size or (file_size - sector_size) % sector_size:
                return None
            sector_count = (file_size - sector_size) // sector_size
            declared_fat_count = struct.unpack_from("<I", prefix, 44)[0]
            declared_fat_ids = [
                value
                for value in struct.unpack_from("<109I", prefix, 76)
                if value != CFB_FREE_SECTOR
            ]
            if not declared_fat_ids or declared_fat_count > 109:
                return None

            entries_per_sector = sector_size // 4
            fat_ids = [declared_fat_ids[0]]
            index = 0
            while index < len(fat_ids):
                fat_sector = fat_ids[index]
                if fat_sector >= sector_count:
                    return None
                source.seek(sector_size + fat_sector * sector_size)
                raw_fat = source.read(sector_size)
                if len(raw_fat) != sector_size:
                    return None
                values = struct.unpack(f"<{entries_per_sector}I", raw_fat)
                base_sector = index * entries_per_sector
                for offset, value in enumerate(values):
                    if value != CFB_FAT_SECTOR:
                        continue
                    referenced_fat = base_sector + offset
                    if referenced_fat >= sector_count:
                        return None
                    if referenced_fat not in fat_ids:
                        fat_ids.append(referenced_fat)
                if len(fat_ids) > 109:
                    return None
                index += 1
    except (OSError, struct.error):
        return None
    return fat_ids if len(fat_ids) > declared_fat_count else None


@contextmanager
def recovered_ole_path(path: Path) -> Iterator[tuple[Path, list[str]]]:
    """Entrega el original o una copia temporal con su firma, su DIFAT y su MiniFAT reparadas."""
    header = _read_header(path)
    lost_signature = signature_lost(header)
    fat_ids = recover_fat_sectors(path)
    lost_minifat = minifat_lost(header)
    if not lost_signature and fat_ids is None and not lost_minifat:
        yield path, []
        return

    with TemporaryDirectory(prefix="ole-recovery-") as directory:
        recovered_path = Path(directory) / "recovered.msg"
        shutil.copyfile(path, recovered_path)
        notices: list[str] = []
        with recovered_path.open("r+b") as target:
            header = bytearray(target.read(_HEADER_SIZE))
            if lost_signature:
                header[:8] = CFB_SIGNATURE
                notices.append(_SIGNATURE_NOTICE)
            if fat_ids is not None:
                struct.pack_into("<I", header, 44, len(fat_ids))
                header_fat_ids = fat_ids + [CFB_FREE_SECTOR] * (109 - len(fat_ids))
                struct.pack_into("<109I", header, 76, *header_fat_ids)
                notices.append(_FAT_NOTICE)
            target.seek(0)
            target.write(header)
        if lost_minifat:
            notices.extend(_restore_minifat(recovered_path))
        yield recovered_path, notices


def _restore_minifat(copy: Path) -> list[str]:
    """Escribe en la copia, ya con firma y FAT repuestas, la única MiniFAT que encaja."""
    location = locate_minifat(copy)
    if location is None:
        return []
    with copy.open("r+b") as target:
        target.seek(_MINIFAT_FIELDS)
        target.write(struct.pack("<II", location.start, location.count))
    return [_MINIFAT_NOTICE]
