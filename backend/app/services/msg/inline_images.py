"""Reconstrucción de la posición de imágenes incrustadas cuando el daño borró sus Content-ID.

El HTML de Outlook declara en cada ``<img src="cid:…">`` su ancho y alto. Si un adjunto sin
Content-ID tiene exactamente esas medidas en píxeles, o es el único con la misma proporción (y nadie
más compite por él), se le asigna ese ``cid`` y se marca como inferido. Ante cualquier ambigüedad no
se asigna: preferimos una imagen sin posición a una imagen en el lugar equivocado.
"""

import re
from dataclasses import dataclass

from app.models.schemas import AttachmentMetadata

#: Diferencia máxima de proporción (ancho/alto) para considerar dos imágenes la misma.
ASPECT_TOLERANCE = 0.01
_IMG = re.compile(r"<img\b[^>]*>", re.IGNORECASE)
_CID = re.compile(r"""\bsrc\s*=\s*["']?cid:([^"'\s>]+)""", re.IGNORECASE)
_DIMENSIONS = re.compile(r"(\d+)\s*[×x]\s*(\d+)")


@dataclass(frozen=True)
class InlineTag:
    cid: str
    width: int | None
    height: int | None


def inline_tags(html: str) -> list[InlineTag]:
    """Etiquetas ``<img>`` con ``cid:`` en orden de aparición, con sus medidas declaradas."""
    tags = []
    for tag in _IMG.findall(html):
        cid = _CID.search(tag)
        if cid:
            tags.append(
                InlineTag(cid.group(1), _attribute(tag, "width"), _attribute(tag, "height"))
            )
    return tags


def assign_by_size(attachments: list[AttachmentMetadata], tags: list[InlineTag]) -> int:
    """Asigna ``content_id`` por medidas a adjuntos que no lo tienen. Devuelve cuántos asignó."""
    known = {item.content_id.lower() for item in attachments if item.content_id}
    wanted = {}
    for tag in tags:
        if tag.width and tag.height and tag.cid.lower() not in known:
            wanted.setdefault(tag.cid, (tag.width, tag.height))
    free = {
        index: size
        for index, item in enumerate(attachments)
        if not item.content_id and (size := _pixels(item))
    }
    assigned = 0
    # Cada pasada se calcula después de la anterior: lo ya emparejado no compite en la siguiente.
    for matcher in (_exact_matches, _aspect_matches):
        for cid, index in _unique_pairs(matcher(wanted, free)).items():
            attachments[index].content_id = cid
            attachments[index].content_id_inferred = True
            wanted.pop(cid, None)
            free.pop(index, None)
            assigned += 1
    return assigned


def _exact_matches(
    wanted: dict[str, tuple[int, int]], free: dict[int, tuple[int, int]]
) -> dict[str, list[int]]:
    return {cid: [i for i, px in free.items() if px == size] for cid, size in wanted.items()}


def _aspect_matches(
    wanted: dict[str, tuple[int, int]], free: dict[int, tuple[int, int]]
) -> dict[str, list[int]]:
    """Misma proporción y resolución suficiente: Outlook reduce las imágenes, no las amplía."""
    matches = {}
    for cid, (width, height) in wanted.items():
        ratio = width / height
        matches[cid] = [
            index
            for index, (px_width, px_height) in free.items()
            if abs(px_width / px_height - ratio) / ratio <= ASPECT_TOLERANCE
            and px_width >= width * 0.95
            and px_height >= height * 0.95
        ]
    return matches


def _unique_pairs(matches: dict[str, list[int]]) -> dict[str, int]:
    """Sólo pares inequívocos: un único candidato para el cid y ningún otro cid que lo quiera."""
    demand: dict[int, int] = {}
    for candidates in matches.values():
        for index in candidates:
            demand[index] = demand.get(index, 0) + 1
    return {
        cid: candidates[0]
        for cid, candidates in matches.items()
        if len(candidates) == 1 and demand[candidates[0]] == 1
    }


def _pixels(attachment: AttachmentMetadata) -> tuple[int, int] | None:
    for item in attachment.metadata:
        if item.group == "Imagen" and item.label == "Dimensiones":
            match = _DIMENSIONS.search(item.value)
            if match and int(match.group(2)):
                return int(match.group(1)), int(match.group(2))
    return None


def _attribute(tag: str, name: str) -> int | None:
    match = re.search(rf"""\b{name}\s*=\s*["']?(\d+)""", tag, re.IGNORECASE)
    return int(match.group(1)) if match and int(match.group(1)) > 0 else None
