"""Recuperación de PNG y PDF completos que sobreviven fuera de los enlaces OLE dañados."""

import hashlib
import struct
import zlib
from dataclasses import dataclass
from pathlib import Path

import olefile

from app.models.schemas import AttachmentMetadata
from app.services.msg.attachments import attachment_from_payload
from app.services.msg.ole_reader import ATTACHMENT_DATA_STREAM, attachment_directories


@dataclass(frozen=True)
class RawAttachment:
    offset: int
    size: int
    name: str
    content_type: str


def _signature_offsets(path: Path, signature: bytes) -> list[int]:
    """Busca una firma por bloques para no cargar el MSG completo en memoria."""
    offsets: list[int] = []
    tail = b""
    position = 0
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            data = tail + chunk
            start = 0
            while (found := data.find(signature, start)) >= 0:
                offsets.append(position - len(tail) + found)
                start = found + 1
            tail = data[-(len(signature) - 1) :]
            position += len(chunk)
    return offsets


def _png_size(source: object, offset: int, file_size: int) -> int | None:
    source.seek(offset + 8)
    first_chunk = True
    while source.tell() + 12 <= file_size:
        chunk_header = source.read(8)
        if len(chunk_header) != 8:
            return None
        chunk_size = struct.unpack(">I", chunk_header[:4])[0]
        chunk_type = chunk_header[4:]
        end = source.tell() + chunk_size + 4
        if end > file_size:
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


def _pdf_size(source: object, offset: int) -> int | None:
    source.seek(offset)
    tail = b""
    position = offset
    end: int | None = None
    while chunk := source.read(1024 * 1024):
        data = tail + chunk
        search_from = 0
        while (found := data.find(b"%%EOF", search_from)) >= 0:
            end = position - len(tail) + found + len(b"%%EOF")
            search_from = found + 1
        tail = data[-4:]
        position += len(chunk)
    return end - offset if end is not None else None


def _range_digest(path: Path, offset: int, size: int) -> bytes:
    digest = hashlib.sha256()
    remaining = size
    with path.open("rb") as source:
        source.seek(offset)
        while remaining:
            chunk = source.read(min(1024 * 1024, remaining))
            if not chunk:
                raise OSError("rango de adjunto incompleto")
            digest.update(chunk)
            remaining -= len(chunk)
    return digest.digest()


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
                    while chunk := source.read(1024 * 1024):
                        digest.update(chunk)
                digests.add(digest.digest())
    except Exception:
        pass
    return digests


def raw_attachment_candidates(path: Path, known_digests: set[bytes]) -> list[RawAttachment]:
    """Encuentra PDF y PNG continuos que sobreviven fuera del arbol OLE dañado."""
    file_size = path.stat().st_size
    candidates: list[tuple[int, int, str, str]] = []
    with path.open("rb") as source:
        for offset in _signature_offsets(path, b"\x89PNG\r\n\x1a\n"):
            size = _png_size(source, offset, file_size)
            if size:
                candidates.append((offset, size, "imagen", "image/png"))
        for offset in _signature_offsets(path, b"%PDF-"):
            size = _pdf_size(source, offset)
            if size:
                candidates.append((offset, size, "documento", "application/pdf"))

    recovered: list[RawAttachment] = []
    counts: dict[str, int] = {}
    for offset, size, label, content_type in sorted(candidates):
        try:
            if _range_digest(path, offset, size) in known_digests:
                continue
        except OSError:
            continue
        counts[label] = counts.get(label, 0) + 1
        extension = ".png" if content_type == "image/png" else ".pdf"
        recovered.append(
            RawAttachment(
                offset=offset,
                size=size,
                name=f"{label}-recuperado-{counts[label]}{extension}",
                content_type=content_type,
            )
        )
    return recovered


def raw_recovered_attachments(path: Path, external_deadline: float) -> list[AttachmentMetadata]:
    attachments: list[AttachmentMetadata] = []
    for candidate in raw_attachment_candidates(path, ole_attachment_digests(path)):
        try:
            with path.open("rb") as source:
                source.seek(candidate.offset)
                payload = source.read(candidate.size)
            if len(payload) != candidate.size:
                continue
            attachment = attachment_from_payload(candidate.name, payload, external_deadline)
            attachment.warnings.insert(
                0,
                "Archivo recuperado de datos legibles del MSG.",
            )
            attachments.append(attachment)
        except Exception:
            continue
    return attachments
