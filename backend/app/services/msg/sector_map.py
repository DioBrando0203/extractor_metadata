"""Partes del archivo que ocupan los streams que el árbol OLE todavía alcanza.

Un archivo "suelto" es el que vive donde ningún stream legible llega. Sin este mapa, una imagen
guardada dentro de un DOCX adjunto o la miniatura EXIF de un JPEG adjunto se tomarían por adjuntos
sueltos. Los streams pequeños viven en mini sectores de 64 bytes dentro del mini stream (la cadena
de la raíz): ahí sólo cuenta como legible el mini sector que un stream alcanzable reclama, porque un
adjunto pequeño que perdió su entrada de directorio sigue en el mini stream.
"""

from dataclasses import dataclass
from pathlib import Path

import olefile


@dataclass(frozen=True)
class SectorMap:
    sector_size: int
    mini_sector_size: int
    #: Sectores normales de streams alcanzables.
    covered: frozenset[int]
    #: Sector del mini stream → su posición en la cadena de la raíz.
    mini_container: dict[int, int]
    #: Mini sectores de streams pequeños alcanzables.
    mini_covered: frozenset[int]

    def covers(self, offset: int) -> bool:
        """La posición cae en datos de un stream legible (el sector 0 sigue a la cabecera)."""
        sector = offset // self.sector_size - 1
        if sector in self.covered:
            return True
        position = self.mini_container.get(sector)
        if position is None:
            return False
        inside = position * self.sector_size + offset % self.sector_size
        return inside // self.mini_sector_size in self.mini_covered


def readable_sectors(path: Path) -> SectorMap | None:
    """Mapa de los streams alcanzables desde la raíz; ``None`` si el contenedor no abre."""
    try:
        with olefile.OleFileIO(str(path)) as container:
            container.loadminifat()
            covered: set[int] = set()
            mini_covered: set[int] = set()
            for entry in container.direntries:
                if entry is None or entry.entry_type != olefile.STGTY_STREAM:
                    continue
                if entry.size >= container.minisectorcutoff:
                    covered.update(_chain(container.fat, entry.isectStart))
                else:
                    mini_covered.update(_chain(container.minifat, entry.isectStart))
            root_chain = _chain(container.fat, container.root.isectStart)
            return SectorMap(
                sector_size=container.sectorsize,
                mini_sector_size=container.minisectorsize,
                covered=frozenset(covered),
                mini_container={sector: index for index, sector in enumerate(root_chain)},
                mini_covered=frozenset(mini_covered),
            )
    except Exception:
        return None


def _chain(table: list[int], start: int) -> list[int]:
    """Sigue una cadena de la FAT o la MiniFAT; se detiene en un fin, un valor fuera de rango o un
    ciclo."""
    chain: list[int] = []
    seen: set[int] = set()
    sector = start
    while sector < len(table) and sector not in seen:
        seen.add(sector)
        chain.append(sector)
        sector = table[sector]
    return chain
