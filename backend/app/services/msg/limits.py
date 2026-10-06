"""Presupuesto de tamaño de la respuesta: miniaturas y metadatos que caben en el JSON."""

from app.core.config import settings
from app.models.schemas import MessageMetadata


def limit_response(message: MessageMetadata) -> MessageMetadata:
    # Las miniaturas son accesorias: se omiten las que excedan el presupuesto sin marcar parcial.
    preview_budget = settings.max_total_preview_chars
    for attachment in message.attachments:
        if attachment.preview is None:
            continue
        if len(attachment.preview) > preview_budget:
            attachment.preview = None
            attachment.preview_source = None
        else:
            preview_budget -= len(attachment.preview)
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
