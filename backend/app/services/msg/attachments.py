"""Enumeración de adjuntos desde el parser MSG o directamente desde el árbol OLE.

Antes de leer bytes se mira cómo viaja cada adjunto (``attachment_entries``): un correo adjunto se
abre con la función que aporta ``reader``, una referencia a la nube o a una ruta se informa como
enlace y el resto se lee como archivo.
"""

import mimetypes
import time
from collections.abc import Callable
from dataclasses import dataclass
from functools import partial
from pathlib import Path

import olefile

from app.models.schemas import AttachmentMetadata, MetadataItem
from app.services.metadata import extract_file_metadata
from app.services.msg.attachment_entries import (
    ATTACHMENT_DATA_STREAM,
    OleAttachment,
    attachment_directories,
)
from app.services.msg.text import clean_text, normalize_content_id, read_attribute
from app.services.previews import thumbnail_data_uri

_ENUMERATION_FAILED = "No se pudo enumerar los adjuntos del mensaje."
_UNREADABLE = "Adjunto ilegible o corrupto: se conserva el resto del mensaje."
_OLE_OBJECT = "Objeto incrustado (OLE): no se expande en esta versión."
_NO_FILE = "Adjunto sin archivo propio: esta versión no puede abrirlo."
_LINK_WITHOUT_ADDRESS = "Archivo en la nube o en una ruta: su dirección no se pudo leer."
_GENERIC_EXTENSIONS = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": ".pptx",
}


@dataclass(frozen=True)
class AttachmentSources:
    """Lo que la lectura de adjuntos necesita además del correo (Parameter Object)."""

    #: Carpeta OLE → descriptor leído sin abrir el adjunto.
    info: dict[str, OleAttachment]
    #: Plazo para metadatos externos y miniaturas.
    deadline: float
    #: Abre el correo adjunto de una carpeta; lo aporta ``reader``, que sabe leer un MSG.
    open_message: Callable[[str, OleAttachment], AttachmentMetadata]

    def describe(self, directory: str, position: int) -> OleAttachment:
        return self.info.get(directory) or OleAttachment(f"adjunto-{position}", 0)


def attachment_from_payload(
    name: str,
    payload: bytes,
    external_deadline: float,
    *,
    recovered: bool = False,
    content_id: str | None = None,
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
        extension = _GENERIC_EXTENSIONS.get(content_type or "")
        if extension:
            name += extension
            for item in metadata:
                if item.group == "Archivo" and item.label == "Nombre":
                    item.value = name
                    break
    preview, preview_source = (None, None)
    if time.monotonic() < external_deadline:
        preview, preview_source = thumbnail_data_uri(payload, name)
    return AttachmentMetadata(
        name=name,
        content_type=content_type,
        size_bytes=len(payload),
        metadata=metadata,
        warnings=attachment_warnings,
        preview=preview,
        preview_source=preview_source,
        content_id=content_id,
    )


def link_attachment(info: OleAttachment) -> AttachmentMetadata:
    """Archivo que vive en una ruta o en la nube: se informa su dirección; no hay bytes."""
    attachment = AttachmentMetadata(
        name=info.name, kind="link", content_type=mimetypes.guess_type(info.name)[0]
    )
    if not info.reference:
        attachment.warnings.append(_LINK_WITHOUT_ADDRESS)
        return attachment
    attachment.link = info.reference
    attachment.metadata.append(
        MetadataItem(group="Enlace", label="Ubicación", value=info.reference)
    )
    return attachment


def without_bytes(
    directory: str, info: OleAttachment, sources: AttachmentSources
) -> AttachmentMetadata | None:
    """Adjuntos que no traen un archivo propio; ``None`` si hay que leerlo como archivo."""
    if info.has_data:
        return None
    if info.is_message:
        return sources.open_message(directory, info)
    if info.is_reference:
        return link_attachment(info)
    if info.has_storage:
        return AttachmentMetadata(name=info.name, warnings=[_OLE_OBJECT])
    return None


def extract_parsed_attachments(
    message: object, warnings: list[str], sources: AttachmentSources
) -> list[AttachmentMetadata]:
    """Inicializa y libera cada adjunto sin descartar archivos por su tamaño."""
    list_dir = read_attribute(message, "listDir", warnings)
    init_attachment = read_attribute(message, "initAttachmentFunc", warnings)
    if not callable(list_dir) or not callable(init_attachment):
        warnings.append(_ENUMERATION_FAILED)
        return []
    try:
        attachment_dirs = attachment_directories(list_dir(False, True, False))
    except Exception:
        warnings.append(_ENUMERATION_FAILED)
        return []
    attachments: list[AttachmentMetadata] = []
    for index, directory in enumerate(attachment_dirs, start=1):
        info = sources.describe(directory, index)
        attachments.append(
            without_bytes(directory, info, sources)
            or _parsed_file(partial(init_attachment, message, directory), info, sources, warnings)
        )
    return attachments


def _parsed_file(
    open_attachment: Callable[[], object],
    info: OleAttachment,
    sources: AttachmentSources,
    warnings: list[str],
) -> AttachmentMetadata:
    """Un adjunto del parser; ``Attachment`` retiene sus bytes y se libera al salir de aquí."""
    name = info.name
    try:
        attachment = open_attachment()
        name = (
            clean_text(read_attribute(attachment, "longFilename", warnings))
            or clean_text(read_attribute(attachment, "shortFilename", warnings))
            or name
        )
        payload = attachment.data
        if not isinstance(payload, bytes):
            return AttachmentMetadata(name=name, warnings=[_NO_FILE])
        content_id = normalize_content_id(clean_text(read_attribute(attachment, "cid", warnings)))
        return attachment_from_payload(
            name, payload, sources.deadline, content_id=content_id or info.content_id
        )
    except Exception:
        return AttachmentMetadata(name=name, size_bytes=info.size or None, warnings=[_UNREADABLE])


def extract_ole_attachments(path: Path, sources: AttachmentSources) -> list[AttachmentMetadata]:
    """Recupera adjuntos si el parser MSG falla pero el árbol OLE sigue legible."""
    attachments: list[AttachmentMetadata] = []
    try:
        with olefile.OleFileIO(str(path)) as container:
            attachment_dirs = attachment_directories(container.listdir())
            for index, directory in enumerate(attachment_dirs, start=1):
                info = sources.describe(directory, index)
                attachments.append(
                    without_bytes(directory, info, sources)
                    or _ole_file(container, directory, info, sources.deadline)
                )
    except Exception:
        return attachments
    return attachments


def _ole_file(
    container: olefile.OleFileIO, directory: str, info: OleAttachment, deadline: float
) -> AttachmentMetadata:
    stream_path = [directory, ATTACHMENT_DATA_STREAM]
    try:
        if not container.exists(stream_path):
            raise OSError("stream de adjunto ausente")
        with container.openstream(stream_path) as stream:
            payload = stream.read()
        return attachment_from_payload(
            info.name, payload, deadline, recovered=True, content_id=info.content_id
        )
    except Exception:
        return AttachmentMetadata(
            name=info.name, size_bytes=info.size or None, warnings=[_UNREADABLE]
        )
