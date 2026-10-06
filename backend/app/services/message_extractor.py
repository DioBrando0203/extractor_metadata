"""Lectura MSG tolerante: contenido humano, propiedades MAPI y recuperación OLE."""

import codecs
import hashlib
import mimetypes
import re
import shutil
import struct
import time
import zlib
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date, datetime
from email.utils import parsedate_to_datetime
from enum import Enum
from itertools import islice
from pathlib import Path
from tempfile import TemporaryDirectory

import extract_msg
import olefile
from extract_msg.enums import ErrorBehavior

from app.core.config import settings
from app.core.errors import ExtractionError
from app.models.schemas import AttachmentMetadata, MessageMetadata, MetadataItem
from app.services.body_text import html_to_text
from app.services.file_metadata import extract_file_metadata

_INVALID_NAME = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_RESERVED_NAME = re.compile(r"^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\.|$)", re.I)
_CFB_SIGNATURE = bytes.fromhex("D0CF11E0A1B11AE1")
_CFB_FREE_SECTOR = 0xFFFFFFFF
_CFB_FAT_SECTOR = 0xFFFFFFFD
_MAPI_LABELS = {
    "001A": "Clase de mensaje",
    "0037": "Asunto",
    "007D": "Encabezados de transporte",
    "0C1A": "Nombre del remitente",
    "0C1F": "Correo del remitente",
    "0E02": "CCO",
    "0E03": "CC",
    "0E04": "Destinatarios",
    "1000": "Cuerpo de texto",
    "1035": "Message-ID",
    "3001": "Nombre",
    "3003": "Dirección",
    "3704": "Nombre corto del adjunto",
    "3707": "Nombre del adjunto",
    "370E": "MIME del adjunto",
}


@dataclass(frozen=True)
class _RawAttachment:
    offset: int
    size: int
    name: str
    content_type: str


def _recover_fat_sectors(path: Path) -> list[int] | None:
    """Reconstruye una DIFAT truncada cuando sus FAT aún se enlazan entre sí.

    Algunos MSG dañados conservan todos sus streams pero declaran menos FAT de
    los que el propio mapa marca. Sólo se acepta CFB v3/v4 con sectores y
    referencias verificables; el contenido no se altera.
    """
    try:
        with path.open("rb") as source:
            prefix = source.read(512)
            if len(prefix) != 512 or prefix[:8] != _CFB_SIGNATURE:
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
                if value != _CFB_FREE_SECTOR
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
                    if value != _CFB_FAT_SECTOR:
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
def _recovered_ole_path(path: Path) -> Iterator[tuple[Path, list[str]]]:
    """Entrega el original o una copia temporal con su DIFAT recuperada."""
    fat_ids = _recover_fat_sectors(path)
    if fat_ids is None:
        yield path, []
        return

    with TemporaryDirectory(prefix="ole-recovery-") as directory:
        recovered_path = Path(directory) / "recovered.msg"
        shutil.copyfile(path, recovered_path)
        with recovered_path.open("r+b") as target:
            header = bytearray(target.read(512))
            struct.pack_into("<I", header, 44, len(fat_ids))
            header_fat_ids = fat_ids + [_CFB_FREE_SECTOR] * (109 - len(fat_ids))
            struct.pack_into("<109I", header, 76, *header_fat_ids)
            target.seek(0)
            target.write(header)
        yield (
            recovered_path,
            ["Se recuperó la tabla FAT en una copia temporal; el MSG original no fue modificado."],
        )


def _text(value: object | None, limit: int = settings.max_property_chars) -> str | None:
    if value is None:
        return None
    if isinstance(value, bytes):
        return f"Binario: {len(value):,} bytes (contenido omitido)"
    if isinstance(value, Enum):
        value = value.name
    if isinstance(value, (datetime, date)):
        value = value.isoformat()
    text = str(value).strip()
    if len(text) > limit:
        text = text[:limit] + f" … [truncado; {len(text):,} caracteres]"
    return text or None


def _filename_warnings(filename: str) -> list[str]:
    warnings: list[str] = []
    if (
        _INVALID_NAME.search(filename)
        or _RESERVED_NAME.match(filename)
        or filename.rstrip(". ") != filename
    ):
        warnings.append(
            "El nombre puede ser incompatible con Windows. Este análisis usa una "
            "copia temporal de nombre corto; para Outlook pruebe renombrar el original."
        )
    if len(filename) > 150:
        warnings.append("Nombre muy largo: puede superar límites de ruta al abrirlo en Windows.")
    return warnings


def _read_attribute(message: object, name: str, warnings: list[str]) -> object | None:
    try:
        return getattr(message, name, None)
    except Exception:
        warnings.append(
            f"No se pudo recuperar la propiedad {name}; se conserva el resto del mensaje."
        )
        return None


def _read_ole_metadata(
    path: Path,
) -> tuple[list[MetadataItem], dict[str, str], list[str], dict[str, tuple[str, int]]]:
    """Lee streams acotados, sin devolver binarios; sirve también de recuperación parcial."""
    items: list[MetadataItem] = []
    recovered: dict[str, str] = {}
    attachment_info: dict[str, tuple[str, int]] = {}
    warnings: list[str] = []
    try:
        with olefile.OleFileIO(str(path)) as container:
            streams = container.listdir()
            for parts in streams:
                if (
                    len(parts) == 2
                    and parts[0].startswith("__attach")
                    and parts[-1] == "__substg1.0_37010102"
                ):
                    try:
                        name = f"adjunto-{len(attachment_info) + 1}"
                        name_path = [parts[0], "__substg1.0_3707001F"]
                        if container.exists(name_path):
                            with container.openstream(name_path) as name_stream:
                                candidate_name = (
                                    name_stream.read(1024)
                                    .decode("utf-16-le", errors="replace")
                                    .rstrip("\x00")
                                )
                                if candidate_name:
                                    name = candidate_name
                        attachment_info[parts[0]] = (name, container.get_size(parts))
                    except Exception:
                        warnings.append("Un adjunto tiene estructura OLE incompleta.")
            ansi_encoding = "cp1252"
            if container.exists("__properties_version1.0"):
                try:
                    raw_props = container.openstream("__properties_version1.0").read(
                        32 + settings.max_properties * 16
                    )
                    for offset in range(32, len(raw_props) - 15, 16):
                        tag = struct.unpack_from("<I", raw_props, offset)[0]
                        if tag == 0x3FFD0003:
                            codepage = struct.unpack_from("<I", raw_props, offset + 8)[0]
                            try:
                                ansi_encoding = codecs.lookup(f"cp{codepage}").name
                            except LookupError:
                                warnings.append(
                                    "Página de códigos desconocida; recuperación ANSI aproximada."
                                )
                            break
                except Exception:
                    warnings.append(
                        "La página de códigos OLE es ilegible; se recupera texto aproximado."
                    )
            if not any(parts[-1].startswith("__substg1.0_") for parts in streams):
                raise ExtractionError(
                    "El archivo OLE no contiene propiedades de un mensaje MSG.", code="NOT_A_MSG"
                )
            if container.parsing_issues:
                warnings.append(
                    "El contenedor OLE presenta inconsistencias; la lectura es parcial."
                )
            for parts in streams[: settings.max_properties]:
                try:
                    name = parts[-1]
                    size = container.get_size(parts)
                    value = f"Binario o estructura: {size:,} bytes (contenido omitido)"
                    if name.startswith("__substg1.0_") and name[-4:] in {"001F", "001E"}:
                        unicode_stream = name.endswith("001F")
                        encoding = "utf-16-le" if unicode_stream else ansi_encoding
                        limit = (settings.max_property_chars + 1) * (2 if unicode_stream else 1)
                        with container.openstream(parts) as stream:
                            data = stream.read(limit)
                        value = data.decode(encoding, errors="replace").rstrip("\x00")
                        if size > limit:
                            value += f" … [truncado; {size:,} bytes]"
                            notice = "Propiedades extensas: algunos valores se muestran abreviados."
                            if notice not in warnings:
                                warnings.append(notice)
                        if len(parts) == 1:
                            recovered[name[12:16]] = value
                    property_id = name[12:16] if name.startswith("__substg1.0_") else ""
                    label = _MAPI_LABELS.get(property_id, name)
                    if len(parts) > 1:
                        label = "/".join(parts[:-1]) + "/" + label
                    items.append(MetadataItem(group="MAPI / OLE", label=label, value=value))
                except Exception:
                    warnings.append(
                        f"Stream OLE ilegible: {'/'.join(parts)}; se conserva el resto."
                    )
            if len(streams) > settings.max_properties:
                warnings.append(
                    f"Se muestran las primeras {settings.max_properties} propiedades OLE."
                )
    except ExtractionError:
        raise
    except Exception as error:
        raise ExtractionError(
            "El contenedor MSG está corrupto o incompleto y no se puede leer.",
            code="INVALID_OR_CORRUPT_MSG",
        ) from error
    return items, recovered, warnings, attachment_info


def _attachment_from_payload(
    name: str, payload: bytes, external_deadline: float, *, recovered: bool = False
) -> AttachmentMetadata:
    content_type, metadata, attachment_warnings = extract_file_metadata(
        payload, name, external_deadline=external_deadline
    )
    if len(payload) > 10 * 1024 * 1024:
        attachment_warnings.insert(
            0,
            "Adjunto mayor de 10 MB: fue leído; el análisis puede tardar más.",
        )
    if recovered:
        attachment_warnings.insert(
            0,
            "Adjunto recuperado directamente de la estructura OLE del MSG.",
        )
    if name.startswith("adjunto-"):
        extension = {
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "application/pdf": ".pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation": ".pptx",
        }.get(content_type or "")
        if extension:
            name += extension
            for item in metadata:
                if item.group == "Archivo" and item.label == "Nombre":
                    item.value = name
                    break
    return AttachmentMetadata(
        name=name,
        content_type=content_type,
        size_bytes=len(payload),
        metadata=metadata,
        warnings=attachment_warnings,
    )


def _attachment_directories(storage_paths: list[list[str]]) -> list[str]:
    directories: list[str] = []
    for parts in storage_paths:
        if parts and parts[0].startswith("__attach") and parts[0] not in directories:
            directories.append(parts[0])
    return directories


def _extract_attachments(
    message: object,
    warnings: list[str],
    attachment_info: dict[str, tuple[str, int]],
    external_deadline: float,
) -> list[AttachmentMetadata]:
    """Inicializa y libera cada adjunto sin descartar archivos por su tamaño."""
    attachments: list[AttachmentMetadata] = []
    list_dir = _read_attribute(message, "listDir", warnings)
    init_attachment = _read_attribute(message, "initAttachmentFunc", warnings)
    if not callable(list_dir) or not callable(init_attachment):
        warnings.append("No se pudo enumerar los adjuntos del mensaje.")
        return attachments
    try:
        attachment_dirs = _attachment_directories(list_dir(False, True, False))
    except Exception:
        warnings.append("No se pudo enumerar los adjuntos del mensaje.")
        return attachments

    for index, attachment_dir in enumerate(attachment_dirs, start=1):
        name, known_size = attachment_info.get(attachment_dir, (f"adjunto-{index}", 0))
        attachment = None
        payload = None
        try:
            attachment = init_attachment(message, attachment_dir)
            name = (
                _text(_read_attribute(attachment, "longFilename", warnings))
                or _text(_read_attribute(attachment, "shortFilename", warnings))
                or name
            )
            payload = attachment.data
            if not isinstance(payload, bytes):
                attachments.append(
                    AttachmentMetadata(
                        name=name,
                        warnings=[
                            "Adjunto MSG anidado u objeto embebido: no se expande en esta versión."
                        ],
                    )
                )
                continue
            attachments.append(_attachment_from_payload(name, payload, external_deadline))
        except Exception:
            attachments.append(
                AttachmentMetadata(
                    name=name,
                    size_bytes=known_size or None,
                    warnings=["Adjunto ilegible o corrupto: se conserva el resto del mensaje."],
                )
            )
        finally:
            # ``Attachment`` conserva ``data`` internamente; se libera antes del siguiente.
            del payload
            del attachment
    return attachments


def _extract_ole_attachments(
    path: Path, attachment_info: dict[str, tuple[str, int]], external_deadline: float
) -> list[AttachmentMetadata]:
    """Recupera adjuntos si el parser MSG falla pero el árbol OLE sigue legible."""
    attachments: list[AttachmentMetadata] = []
    try:
        with olefile.OleFileIO(str(path)) as container:
            attachment_dirs = _attachment_directories(container.listdir())
            for index, attachment_dir in enumerate(attachment_dirs, start=1):
                name, known_size = attachment_info.get(attachment_dir, (f"adjunto-{index}", 0))
                stream_path = [attachment_dir, "__substg1.0_37010102"]
                try:
                    if not container.exists(stream_path):
                        raise OSError("stream de adjunto ausente")
                    with container.openstream(stream_path) as stream:
                        payload = stream.read()
                    attachments.append(
                        _attachment_from_payload(name, payload, external_deadline, recovered=True)
                    )
                except Exception:
                    attachments.append(
                        AttachmentMetadata(
                            name=name,
                            size_bytes=known_size or None,
                            warnings=[
                                "Adjunto ilegible o corrupto: se conserva el resto del mensaje."
                            ],
                        )
                    )
    except Exception:
        return attachments
    return attachments


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


def _ole_attachment_digests(path: Path) -> set[bytes]:
    digests: set[bytes] = set()
    try:
        with olefile.OleFileIO(str(path)) as container:
            for directory in _attachment_directories(container.listdir()):
                stream_path = [directory, "__substg1.0_37010102"]
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


def _raw_attachment_candidates(path: Path, known_digests: set[bytes]) -> list[_RawAttachment]:
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

    recovered: list[_RawAttachment] = []
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
            _RawAttachment(
                offset=offset,
                size=size,
                name=f"{label}-recuperado-{counts[label]}{extension}",
                content_type=content_type,
            )
        )
    return recovered


def _raw_recovered_attachments(path: Path, external_deadline: float) -> list[AttachmentMetadata]:
    attachments: list[AttachmentMetadata] = []
    for candidate in _raw_attachment_candidates(path, _ole_attachment_digests(path)):
        try:
            with path.open("rb") as source:
                source.seek(candidate.offset)
                payload = source.read(candidate.size)
            if len(payload) != candidate.size:
                continue
            attachment = _attachment_from_payload(candidate.name, payload, external_deadline)
            attachment.warnings.insert(
                0,
                "Archivo recuperado de datos legibles del MSG.",
            )
            attachments.append(attachment)
        except Exception:
            continue
    return attachments


def _download_filename(name: str, index: int, header: bytes) -> tuple[str, str]:
    """Devuelve un nombre seguro para un adjunto cuyo nombre MAPI puede faltar."""
    filename = _INVALID_NAME.sub("_", Path(name).name).strip(". ") or f"adjunto-{index + 1}"
    content_type = mimetypes.guess_type(filename)[0]
    if Path(filename).suffix:
        return filename, content_type or "application/octet-stream"
    signatures = (
        (b"\xff\xd8\xff", ".jpg", "image/jpeg"),
        (b"\x89PNG\r\n\x1a\n", ".png", "image/png"),
        (b"%PDF-", ".pdf", "application/pdf"),
    )
    for signature, extension, detected_type in signatures:
        if header.startswith(signature):
            return f"{filename}{extension}", detected_type
    return filename, "application/octet-stream"


def extract_attachment_file(
    path: Path, attachment_index: int, destination: Path
) -> tuple[str, str]:
    """Materializa un adjunto en un temporal de la solicitud, nunca en el original."""
    if attachment_index < 0 or not olefile.isOleFile(str(path)):
        raise ExtractionError("No se encontró el adjunto solicitado.", code="ATTACHMENT_NOT_FOUND")
    with _recovered_ole_path(path) as (read_path, recovery_warnings):
        _items, _recovered, _warnings, attachment_info = _read_ole_metadata(read_path)
        try:
            with olefile.OleFileIO(str(read_path)) as container:
                attachment_dirs = _attachment_directories(container.listdir())
                if attachment_index < len(attachment_dirs):
                    attachment_dir = attachment_dirs[attachment_index]
                    name = attachment_info.get(
                        attachment_dir, (f"adjunto-{attachment_index + 1}", 0)
                    )[0]
                    stream_path = [attachment_dir, "__substg1.0_37010102"]
                    if not container.exists(stream_path):
                        raise ExtractionError(
                            "El adjunto no contiene un archivo que se pueda descargar.",
                            code="UNREADABLE_ATTACHMENT",
                        )
                    with container.openstream(stream_path) as source:
                        header = source.read(32)
                        filename, content_type = _download_filename(name, attachment_index, header)
                        with destination.open("wb") as output:
                            output.write(header)
                            while chunk := source.read(1024 * 1024):
                                output.write(chunk)
                    return filename, content_type

            raw_index = attachment_index - len(attachment_dirs)
            candidates = (
                _raw_attachment_candidates(read_path, _ole_attachment_digests(read_path))
                if recovery_warnings
                else []
            )
            if raw_index < 0 or raw_index >= len(candidates):
                raise ExtractionError(
                    "No se encontró el adjunto solicitado.", code="ATTACHMENT_NOT_FOUND"
                )
            candidate = candidates[raw_index]
            with read_path.open("rb") as source, destination.open("wb") as output:
                source.seek(candidate.offset)
                remaining = candidate.size
                while remaining:
                    chunk = source.read(min(1024 * 1024, remaining))
                    if not chunk:
                        raise ExtractionError(
                            "El adjunto recuperado está incompleto.", code="UNREADABLE_ATTACHMENT"
                        )
                    output.write(chunk)
                    remaining -= len(chunk)
            return candidate.name, candidate.content_type
        except ExtractionError:
            raise
        except Exception as error:
            raise ExtractionError(
                "No fue posible preparar el adjunto para descargar.", code="UNREADABLE_ATTACHMENT"
            ) from error


def _fixed_properties(message: object, warnings: list[str]) -> list[MetadataItem]:
    result: list[MetadataItem] = []
    store = _read_attribute(message, "props", warnings)
    if store is None:
        return result
    try:
        for tag, prop in islice(store.items(), settings.max_properties):
            # Los valores variables ya se muestran desde sus streams OLE.
            if hasattr(prop, "value"):
                value = _text(prop.value)
                if value is not None:
                    result.append(
                        MetadataItem(group="Propiedades MAPI", label=f"0x{tag}", value=value)
                    )
    except Exception:
        warnings.append("Algunas propiedades MAPI fijas no pudieron leerse.")
    return result


def _limit_response(message: MessageMetadata) -> MessageMetadata:
    remaining = settings.max_total_metadata_chars
    for collection in [
        message.properties,
        message.headers,
        *(attachment.metadata for attachment in message.attachments),
    ]:
        keep = []
        for item in collection:
            size = len(item.group) + len(item.label) + len(item.value)
            if size <= remaining:
                keep.append(item)
                remaining -= size
        if len(keep) < len(collection):
            if (
                "Metadata extensa: se omitieron campos por el límite total de respuesta."
                not in message.warnings
            ):
                message.warnings.append(
                    "Metadata extensa: se omitieron campos por el límite total de respuesta."
                )
            message.status = "partial"
            collection[:] = keep
    return message


def extract_msg_file(path: Path, original_name: str, size_bytes: int) -> MessageMetadata:
    if not olefile.isOleFile(str(path)):
        raise ExtractionError(
            "El archivo no tiene una firma MSG/OLE válida. Puede estar corrupto "
            "o haber sido renombrado desde otro formato.",
            code="INVALID_OR_CORRUPT_MSG",
        )
    with _recovered_ole_path(path) as (read_path, recovery_warnings):
        return _extract_msg_contents(read_path, original_name, size_bytes, recovery_warnings)


def _extract_msg_contents(
    path: Path, original_name: str, size_bytes: int, recovery_warnings: list[str]
) -> MessageMetadata:
    started = time.monotonic()
    properties, recovered, ole_warnings, attachment_info = _read_ole_metadata(path)
    warnings = _filename_warnings(original_name) + recovery_warnings + ole_warnings
    try:
        message = extract_msg.openMsg(
            str(path),
            delayAttachments=True,
            errorBehavior=(
                ErrorBehavior.ATTACH_NOT_IMPLEMENTED
                | ErrorBehavior.ATTACH_BROKEN
                | ErrorBehavior.STANDARDS_VIOLATION
                | ErrorBehavior.OLE_DEFECT_INCORRECT
            ),
        )
    except Exception:
        if not any(recovered.get(key) for key in ("0037", "1000", "0C1A", "0C1F")):
            raise ExtractionError(
                "El contenedor abre, pero no se pudo recuperar contenido del MSG.",
                code="UNREADABLE_MSG",
            ) from None
        warnings.append(
            "El lector MSG falló. Se recuperaron propiedades desde OLE y los adjuntos "
            "que permanecen legibles."
        )
        body = recovered.get("1000")
        attachments = _extract_ole_attachments(path, attachment_info, started + 30)
        if recovery_warnings:
            attachments.extend(_raw_recovered_attachments(path, started + 30))
        if any(item.warnings for item in attachments):
            warnings.append("Uno o más adjuntos tienen advertencias; consulta la pestaña Adjuntos.")
        return _limit_response(
            MessageMetadata(
                file_name=original_name,
                file_size_bytes=size_bytes,
                subject=recovered.get("0037"),
                sender=recovered.get("0C1F") or recovered.get("0C1A"),
                recipients=[recovered["0E04"]] if recovered.get("0E04") else [],
                body_preview=body,
                body_truncated=bool(body and "[truncado;" in body),
                properties=properties,
                attachments=attachments,
                warnings=warnings,
                status="partial",
            )
        )

    try:
        subject = _text(_read_attribute(message, "subject", warnings))
        sender = _text(_read_attribute(message, "sender", warnings))
        recipients = []
        for key, label in (("to", "Para"), ("cc", "CC"), ("bcc", "CCO")):
            value = _text(_read_attribute(message, key, warnings))
            if value:
                recipients.append(f"{label}: {value}")
        sent_at = _read_attribute(message, "date", warnings)
        if not isinstance(sent_at, datetime):
            sent_at = None
        body_raw = _read_attribute(message, "body", warnings)
        body = str(body_raw) if body_raw else None
        if not body:
            html = _read_attribute(message, "htmlBody", warnings)
            if isinstance(html, (bytes, str)) and html:
                body = html_to_text(html)
        if not body and recovered.get("1000"):
            body = recovered["1000"]
        received_at = None
        try:
            received_at = message.props.getValue("0E060040")
            if not isinstance(received_at, datetime):
                received_at = None
        except Exception:
            warnings.append("No se pudo recuperar la fecha de recepción.")
        truncated = bool(body and len(body) > settings.max_body_chars)
        if truncated:
            warnings.append(f"Cuerpo largo: se muestran {settings.max_body_chars:,} caracteres.")
        headers: list[MetadataItem] = []
        header = _read_attribute(message, "header", warnings)
        if header is not None:
            try:
                headers = [
                    MetadataItem(group="Encabezado", label=key, value=_text(value) or "")
                    for key, value in list(header.items())[: settings.max_properties]
                ]
                if sent_at is None and header.get("Date"):
                    try:
                        sent_at = parsedate_to_datetime(header.get("Date"))
                    except (TypeError, ValueError, OverflowError):
                        pass
            except Exception:
                warnings.append("Encabezados de transporte parcialmente ilegibles.")
        for key, label in (
            ("classType", "Clase"),
            ("importance", "Importancia"),
            ("stringEncoding", "Codificación"),
            ("messageId", "Message-ID"),
        ):
            value = _text(_read_attribute(message, key, warnings))
            if value:
                properties.insert(0, MetadataItem(group="Mensaje", label=label, value=value))
        properties.extend(_fixed_properties(message, warnings))
        attachments = _extract_attachments(message, warnings, attachment_info, started + 30)
        if recovery_warnings:
            attachments.extend(_raw_recovered_attachments(path, started + 30))
        if any(item.warnings for item in attachments):
            warnings.append("Uno o más adjuntos tienen advertencias; consulta la pestaña Adjuntos.")
        return _limit_response(
            MessageMetadata(
                file_name=original_name,
                file_size_bytes=size_bytes,
                subject=subject,
                sender=sender,
                recipients=recipients,
                sent_at=sent_at,
                received_at=received_at,
                body_preview=body[: settings.max_body_chars] if body else None,
                body_truncated=truncated,
                properties=properties,
                headers=headers,
                attachments=attachments,
                warnings=warnings,
                status="partial" if warnings else "complete",
            )
        )
    finally:
        try:
            message.close()
        except Exception:
            # El proceso finaliza y el SO libera handles; no perder el resultado recuperado.
            pass
