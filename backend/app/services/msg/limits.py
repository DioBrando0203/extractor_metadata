"""Presupuesto de tamaño de la respuesta: miniaturas y metadatos que caben en el JSON.

El presupuesto es uno solo para el correo y todos los correos adjuntos que contiene.
"""

from collections.abc import Iterator

from app.core.config import settings
from app.models.schemas import AttachmentMetadata, MessageMetadata, MetadataItem

_METADATA_NOTICE = "Metadata extensa: se omitieron campos por el límite total de respuesta."


def limit_response(message: MessageMetadata) -> MessageMetadata:
    messages = list(_messages(message))
    _limit_previews([attachment for current in messages for attachment in current.attachments])
    remaining = settings.max_total_metadata_chars
    for current in messages:
        collections = [
            current.properties,
            current.headers,
            *(attachment.metadata for attachment in current.attachments),
        ]
        for collection in collections:
            remaining, cut = _keep_within(collection, remaining)
            if cut:
                if _METADATA_NOTICE not in current.warnings:
                    current.warnings.append(_METADATA_NOTICE)
                current.status = "partial"
    return message


def _messages(message: MessageMetadata) -> Iterator[MessageMetadata]:
    """El correo y, en orden, cada correo adjunto que contiene."""
    yield message
    for attachment in message.attachments:
        if attachment.message is not None:
            yield from _messages(attachment.message)


def _limit_previews(attachments: list[AttachmentMetadata]) -> None:
    # Las miniaturas son accesorias: se omiten las que excedan el presupuesto sin marcar parcial.
    budget = settings.max_total_preview_chars
    for attachment in attachments:
        if attachment.preview is None:
            continue
        if len(attachment.preview) > budget:
            attachment.preview = None
            attachment.preview_source = None
        else:
            budget -= len(attachment.preview)


def _keep_within(collection: list[MetadataItem], remaining: int) -> tuple[int, bool]:
    """Conserva los campos que caben; devuelve el presupuesto restante y si se omitió alguno."""
    keep = []
    for item in collection:
        size = len(item.group) + len(item.label) + len(item.value)
        if size <= remaining:
            keep.append(item)
            remaining -= size
    cut = len(keep) < len(collection)
    collection[:] = keep
    return remaining, cut
