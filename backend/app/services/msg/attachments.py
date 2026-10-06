"""Enumeración de adjuntos desde el parser MSG o directamente desde el árbol OLE."""

import time
from pathlib import Path

import olefile

from app.models.schemas import AttachmentMetadata
from app.services.metadata import extract_file_metadata
from app.services.msg.ole_reader import (
    ATTACHMENT_DATA_STREAM,
    OleAttachment,
    attachment_directories,
)
from app.services.msg.text import clean_text, normalize_content_id, read_attribute
from app.services.previews import thumbnail_data_uri


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


def extract_parsed_attachments(
    message: object,
    warnings: list[str],
    attachment_info: dict[str, OleAttachment],
    external_deadline: float,
) -> list[AttachmentMetadata]:
    """Inicializa y libera cada adjunto sin descartar archivos por su tamaño."""
    attachments: list[AttachmentMetadata] = []
    list_dir = read_attribute(message, "listDir", warnings)
    init_attachment = read_attribute(message, "initAttachmentFunc", warnings)
    if not callable(list_dir) or not callable(init_attachment):
        warnings.append("No se pudo enumerar los adjuntos del mensaje.")
        return attachments
    try:
        attachment_dirs = attachment_directories(list_dir(False, True, False))
    except Exception:
        warnings.append("No se pudo enumerar los adjuntos del mensaje.")
        return attachments

    for index, attachment_dir in enumerate(attachment_dirs, start=1):
        info = attachment_info.get(attachment_dir) or OleAttachment(f"adjunto-{index}", 0)
        name, known_size = info.name, info.size
        attachment = None
        payload = None
        try:
            attachment = init_attachment(message, attachment_dir)
            name = (
                clean_text(read_attribute(attachment, "longFilename", warnings))
                or clean_text(read_attribute(attachment, "shortFilename", warnings))
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
            content_id = normalize_content_id(
                clean_text(read_attribute(attachment, "cid", warnings))
            )
            attachments.append(
                attachment_from_payload(
                    name, payload, external_deadline, content_id=content_id or info.content_id
                )
            )
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


def extract_ole_attachments(
    path: Path, attachment_info: dict[str, OleAttachment], external_deadline: float
) -> list[AttachmentMetadata]:
    """Recupera adjuntos si el parser MSG falla pero el árbol OLE sigue legible."""
    attachments: list[AttachmentMetadata] = []
    try:
        with olefile.OleFileIO(str(path)) as container:
            attachment_dirs = attachment_directories(container.listdir())
            for index, attachment_dir in enumerate(attachment_dirs, start=1):
                info = attachment_info.get(attachment_dir) or OleAttachment(f"adjunto-{index}", 0)
                name, known_size = info.name, info.size
                stream_path = [attachment_dir, ATTACHMENT_DATA_STREAM]
                try:
                    if not container.exists(stream_path):
                        raise OSError("stream de adjunto ausente")
                    with container.openstream(stream_path) as stream:
                        payload = stream.read()
                    attachments.append(
                        attachment_from_payload(
                            name,
                            payload,
                            external_deadline,
                            recovered=True,
                            content_id=info.content_id,
                        )
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
