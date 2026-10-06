"""Recuperación de una DIFAT truncada en una copia temporal; el MSG original nunca se modifica."""

import shutil
import struct
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory

CFB_SIGNATURE = bytes.fromhex("D0CF11E0A1B11AE1")


CFB_FREE_SECTOR = 0xFFFFFFFF


CFB_FAT_SECTOR = 0xFFFFFFFD


def recover_fat_sectors(path: Path) -> list[int] | None:
    """Reconstruye una DIFAT truncada cuando sus FAT aún se enlazan entre sí.

    Algunos MSG dañados conservan todos sus streams pero declaran menos FAT de
    los que el propio mapa marca. Sólo se acepta CFB v3/v4 con sectores y
    referencias verificables; el contenido no se altera.
    """
    try:
        with path.open("rb") as source:
            prefix = source.read(512)
            if len(prefix) != 512 or prefix[:8] != CFB_SIGNATURE:
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
    """Entrega el original o una copia temporal con su DIFAT recuperada."""
    fat_ids = recover_fat_sectors(path)
    if fat_ids is None:
        yield path, []
        return

    with TemporaryDirectory(prefix="ole-recovery-") as directory:
        recovered_path = Path(directory) / "recovered.msg"
        shutil.copyfile(path, recovered_path)
        with recovered_path.open("r+b") as target:
            header = bytearray(target.read(512))
            struct.pack_into("<I", header, 44, len(fat_ids))
            header_fat_ids = fat_ids + [CFB_FREE_SECTOR] * (109 - len(fat_ids))
            struct.pack_into("<109I", header, 76, *header_fat_ids)
            target.seek(0)
            target.write(header)
        yield (
            recovered_path,
            ["Se recuperó la tabla FAT en una copia temporal; el MSG original no fue modificado."],
        )
