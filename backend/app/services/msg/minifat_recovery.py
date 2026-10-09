"""Ubicación de una MiniFAT que la cabecera perdió, para reponerla en una copia (PEN-04).

Los streams de menos de 4096 bytes (asunto, remitente, destinatarios cortos, nombres y Content-ID
de adjuntos) viven en mini sectores de 64 bytes dentro del mini stream y se encadenan con la
MiniFAT. Si la cabecera ya no dice dónde empieza la MiniFAT, todos se leen vacíos aunque sus bytes
sigan en el archivo. La MiniFAT sigue siendo una cadena de la FAT: se acepta un candidato sólo si es
el único cuya tabla explica cada stream pequeño del directorio (cadena del largo exacto que termina
en fin de cadena, sin mini sectores compartidos y dentro de la parte legible del mini stream).

El mini stream se lee siempre por su cadena en la FAT, nunca como bytes contiguos: suponer
contigüidad en un MSG real dio datos falsos. Este módulo no escribe; ``fat_recovery`` aplica el
resultado en la copia temporal.
"""

import math
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO

import olefile

_FREE = 0xFFFFFFFF
_END = 0xFFFFFFFE
#: Valores de la FAT que marcan sectores de la propia FAT o de la DIFAT: no son datos de un stream.
_TABLE_SECTORS = (0xFFFFFFFD, 0xFFFFFFFC)
_MINIFAT_FIELDS = 60


@dataclass(frozen=True)
class MiniFatLocation:
    start: int
    count: int


@dataclass(frozen=True)
class _Layout:
    """Lo que hace falta para validar un candidato, leído del contenedor con la MiniFAT perdida."""

    sector_size: int
    mini_sector_size: int
    fat: list[int]
    #: Mini sectores que declara el mini stream (tamaño de la raíz).
    total_minis: int
    #: Mini sectores alcanzables siguiendo la cadena del mini stream en la FAT.
    readable_minis: int
    #: ``(inicio, tamaño)`` de cada stream pequeño con datos.
    small_streams: list[tuple[int, int]]
    #: Sectores que ya son el inicio de otro stream, del directorio o del mini stream.
    known_starts: frozenset[int]


def minifat_lost(header: bytes) -> bool:
    """La cabecera no dice dónde está la MiniFAT (inicio sin sector o cantidad cero)."""
    if len(header) < _MINIFAT_FIELDS + 8:
        return False
    start, count = struct.unpack_from("<II", header, _MINIFAT_FIELDS)
    return start in (_FREE, _END) or count == 0


def locate_minifat(path: Path) -> MiniFatLocation | None:
    """La única cadena de la FAT que explica todos los streams pequeños; ``None`` si no hay una."""
    layout = _read_layout(path)
    if layout is None or not layout.small_streams:
        return None
    found: list[MiniFatLocation] = []
    with path.open("rb") as source:
        for head in _chain_heads(layout):
            table = _table_from(source, layout, head)
            if table is not None and _explains_streams(table, layout):
                found.append(MiniFatLocation(head, len(table) * 4 // layout.sector_size))
            if len(found) > 1:
                return None  # Dos tablas posibles: no se elige a ciegas.
    return found[0] if found else None


def _read_layout(path: Path) -> _Layout | None:
    try:
        with olefile.OleFileIO(str(path)) as container:
            streams = [
                entry
                for entry in container.direntries
                if entry is not None and entry.entry_type == olefile.STGTY_STREAM
            ]
            cutoff = container.minisectorcutoff
            root = container.root
            fat = list(container.fat)
            sector_size = container.sectorsize
            mini_size = container.minisectorsize
            root_chain = _stream_chain(fat, root.isectStart, math.ceil(root.size / sector_size))
            total_minis = math.ceil(root.size / mini_size)
            return _Layout(
                sector_size=sector_size,
                mini_sector_size=mini_size,
                fat=fat,
                total_minis=total_minis,
                readable_minis=min(len(root_chain) * (sector_size // mini_size), total_minis),
                small_streams=[(e.isectStart, e.size) for e in streams if 0 < e.size < cutoff],
                known_starts=frozenset(
                    {e.isectStart for e in streams if e.size >= cutoff}
                    | {root.isectStart, container.first_dir_sector}
                ),
            )
    except Exception:
        return None


def _stream_chain(fat: list[int], start: int, length: int) -> list[int]:
    """Cadena de un stream hasta ``length`` sectores; corta en un fin, un ciclo o un sector que la
    FAT marca como libre o como tabla (ningún stream los contiene)."""
    chain: list[int] = []
    seen: set[int] = set()
    sector = start
    while (
        len(chain) < length
        and sector < len(fat)
        and sector not in seen
        and fat[sector] not in (_FREE, *_TABLE_SECTORS)
    ):
        seen.add(sector)
        chain.append(sector)
        sector = fat[sector]
    return chain


def _chain_heads(layout: _Layout) -> list[int]:
    """Sectores con datos a los que ninguna entrada de la FAT apunta: inicios de cadena."""
    fat = layout.fat
    targets = {value for value in fat if value < len(fat)}
    return [
        sector
        for sector, value in enumerate(fat)
        if (value < len(fat) or value == _END)
        and sector not in targets
        and sector not in layout.known_starts
    ]


def _table_from(source: BinaryIO, layout: _Layout, head: int) -> list[int] | None:
    """Entradas de la cadena que empieza en ``head`` si todas tienen forma de MiniFAT."""
    entries_per_sector = layout.sector_size // 4
    # Más sectores que los que el mini stream necesita no son una MiniFAT: no se lee de más.
    max_sectors = math.ceil(layout.total_minis / entries_per_sector)
    table: list[int] = []
    sector = head
    for _ in range(max_sectors):
        source.seek((sector + 1) * layout.sector_size)
        raw = source.read(layout.sector_size)
        if len(raw) != layout.sector_size:
            return None
        values = struct.unpack(f"<{entries_per_sector}I", raw)
        if any(v not in (_FREE, _END) and v >= layout.total_minis for v in values):
            return None
        table.extend(values)
        sector = layout.fat[sector]
        if sector == _END:
            return table
        if sector >= len(layout.fat):
            return None
    return None


def _explains_streams(table: list[int], layout: _Layout) -> bool:
    """Cada stream pequeño tiene su cadena exacta, sin compartir mini sectores con otro."""
    limit = min(layout.readable_minis, len(table))
    used: set[int] = set()
    for start, size in layout.small_streams:
        sector = start
        for _ in range(math.ceil(size / layout.mini_sector_size)):
            if sector >= limit or sector in used:
                return False
            used.add(sector)
            sector = table[sector]
        if sector != _END:
            return False
    return True
