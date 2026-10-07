"""Archivos completos que sobreviven sueltos fuera de los enlaces OLE dañados.

Se buscan las firmas de ``raw_formats`` (PNG, JPEG, GIF, PDF y ZIP/Office) y se valida cada una.
Un candidato se descarta si cae en un sector de un stream legible (``sector_map``), si está
dentro de otro ya aceptado (la miniatura de un JPEG, una imagen de un DOCX) o si es idéntico a un
adjunto legible. Análisis y descarga usan ``loose_candidates``: mismo orden, mismos índices.
"""

import hashlib
from dataclasses import dataclass
from pathlib import Path

import olefile

from app.models.schemas import AttachmentMetadata
from app.services.metadata import zip_kind
from app.services.msg.attachment_entries import ATTACHMENT_DATA_STREAM, attachment_directories
from app.services.msg.attachments import attachment_from_payload
from app.services.msg.raw_formats import MAX_RAW_BYTES, RAW_FORMATS, RawFormat
from app.services.msg.sector_map import SectorMap, readable_sectors

_CHUNK = 1024 * 1024
_ZIP = "application/zip"
_RECOVERED = "Archivo recuperado de datos legibles del MSG."


@dataclass(frozen=True)
class RawAttachment:
    offset: int
    size: int
    name: str
    content_type: str


def signature_offsets(path: Path, signature: bytes) -> list[int]:
    """Busca una firma por bloques para no cargar el MSG completo en memoria."""
    offsets: list[int] = []
    tail = b""
    position = 0
    with path.open("rb") as source:
        while chunk := source.read(_CHUNK):
            data = tail + chunk
            start = 0
            while (found := data.find(signature, start)) >= 0:
                offsets.append(position - len(tail) + found)
                start = found + 1
            tail = data[-(len(signature) - 1) :]
            position += len(chunk)
    return offsets


def ole_attachment_digests(path: Path) -> set[bytes]:
    digests: set[bytes] = set()
    try:
        with olefile.OleFileIO(str(path)) as container:
            for directory in attachment_directories(container.listdir()):
                stream_path = [directory, ATTACHMENT_DATA_STREAM]
                if not container.exists(stream_path):
                    continue
                digest = hashlib.sha256()
                with container.openstream(stream_path) as source:
                    while chunk := source.read(_CHUNK):
                        digest.update(chunk)
                digests.add(digest.digest())
    except Exception:
        pass
    return digests


def loose_candidates(path: Path) -> list[RawAttachment]:
    """Archivos sueltos de ``path`` con todas las exclusiones; la descarga usa este mismo orden."""
    return raw_attachment_candidates(path, ole_attachment_digests(path), readable_sectors(path))


def raw_attachment_candidates(
    path: Path, known_digests: set[bytes], sectors: SectorMap | None = None
) -> list[RawAttachment]:
    """Archivos completos y válidos fuera de los streams legibles, en orden de aparición."""
    hits = sorted(
        (
            (offset, raw_format)
            for raw_format in RAW_FORMATS
            for offset in signature_offsets(path, raw_format.signature)
        ),
        key=lambda hit: hit[0],
    )
    file_size = path.stat().st_size
    found: list[tuple[int, int, RawFormat]] = []
    consumed = 0
    with path.open("rb") as source:
        for offset, raw_format in hits:
            if offset < consumed or (sectors is not None and sectors.covers(offset)):
                continue
            size = raw_format.find_size(source, offset, file_size)
            if not size or size > MAX_RAW_BYTES:
                continue
            # Lo que hay dentro de este archivo (aunque sea un adjunto legible) no es otro suelto.
            consumed = offset + size
            if _range_digest(path, offset, size) not in known_digests:
                found.append((offset, size, raw_format))
    return _named(path, found)


def raw_recovered_attachments(path: Path, external_deadline: float) -> list[AttachmentMetadata]:
    attachments: list[AttachmentMetadata] = []
    for candidate in loose_candidates(path):
        try:
            with path.open("rb") as source:
                source.seek(candidate.offset)
                payload = source.read(candidate.size)
            if len(payload) != candidate.size:
                continue
            attachment = attachment_from_payload(candidate.name, payload, external_deadline)
            attachment.warnings.insert(0, _RECOVERED)
            attachments.append(attachment)
        except Exception:
            continue
    return attachments


def _range_digest(path: Path, offset: int, size: int) -> bytes | None:
    digest = hashlib.sha256()
    remaining = size
    with path.open("rb") as source:
        source.seek(offset)
        while remaining:
            chunk = source.read(min(_CHUNK, remaining))
            if not chunk:
                return None
            digest.update(chunk)
            remaining -= len(chunk)
    return digest.digest()


def _named(path: Path, found: list[tuple[int, int, RawFormat]]) -> list[RawAttachment]:
    """Nombre legible por tipo: ``imagen-recuperado-1.png``, ``documento-recuperado-1.docx``."""
    counts: dict[str, int] = {}
    named: list[RawAttachment] = []
    for offset, size, raw_format in found:
        label, extension, content_type = _describe(path, offset, size, raw_format)
        counts[label] = counts.get(label, 0) + 1
        name = f"{label}-recuperado-{counts[label]}{extension}"
        named.append(RawAttachment(offset, size, name, content_type))
    return named


def _describe(path: Path, offset: int, size: int, raw_format: RawFormat) -> tuple[str, str, str]:
    """Un ZIP puede ser Word, Excel o PowerPoint: se reconoce por su directorio interno."""
    if raw_format.content_type != _ZIP:
        return raw_format.label, raw_format.extension, raw_format.content_type
    with path.open("rb") as source:
        source.seek(offset)
        kind = zip_kind(source.read(size))
    if kind is None or kind[0] == "zip":
        return raw_format.label, raw_format.extension, _ZIP
    return "documento", f".{kind[0]}", kind[1] or _ZIP
