"""Orquesta la lectura de un MSG con dos estrategias.

1. Parser ``extract_msg``: lectura completa (remitente, destinatarios, fechas, cuerpo, adjuntos).
2. Recuperación OLE: si el parser falla, se arma el correo con lo que el contenedor aún conserva.

Ambas comparten un ``_ReadContext``. Un correo adjunto se lee con este mismo flujo (``embedded``)
dentro de un presupuesto compartido; ``limit_response`` acota una sola vez la respuesta completa.
"""

import time
from dataclasses import dataclass
from datetime import datetime
from functools import partial
from pathlib import Path

import extract_msg
import olefile
from extract_msg.enums import ErrorBehavior

from app.core.config import settings
from app.core.errors import ExtractionError
from app.models.schemas import AttachmentMetadata, MessageMetadata
from app.services.msg.attachments import (
    AttachmentSources,
    extract_ole_attachments,
    extract_parsed_attachments,
)
from app.services.msg.embedded import EmbeddedBudget, open_embedded_message
from app.services.msg.envelope import Envelope, envelope_from_headers, envelope_from_properties
from app.services.msg.fat_recovery import recovered_ole_path
from app.services.msg.inline_images import assign_by_size
from app.services.msg.limits import limit_response
from app.services.msg.names import filename_warnings
from app.services.msg.ole_reader import OleMetadata, read_ole_metadata
from app.services.msg.parsed_fields import (
    read_body,
    read_fixed_properties,
    read_headers,
    read_message_properties,
    read_received_at,
    read_recipients,
)
from app.services.msg.raw_body import best_recovered_body
from app.services.msg.raw_recovery import raw_recovered_attachments
from app.services.msg.text import clean_text, read_attribute

#: Presupuesto para herramientas externas y miniaturas de adjuntos, contado desde el inicio.
ATTACHMENT_BUDGET_SECONDS = 30
_PARSER_ERRORS = (
    ErrorBehavior.ATTACH_NOT_IMPLEMENTED
    | ErrorBehavior.ATTACH_BROKEN
    | ErrorBehavior.STANDARDS_VIOLATION
    | ErrorBehavior.OLE_DEFECT_INCORRECT
)
#: Propiedades MAPI que justifican devolver un correo recuperado: asunto, cuerpo, remitente o
#: encabezados de transporte (que resisten daños del mini stream).
_RECOVERABLE_KEYS = ("0037", "1000", "0C1A", "0C1F", "007D")
_ATTACHMENT_NOTICE = "Uno o más adjuntos tienen advertencias; consulta la pestaña Adjuntos."


@dataclass
class _ReadContext:
    """Datos comunes a las dos estrategias de lectura."""

    path: Path
    original_name: str
    size_bytes: int
    ole: OleMetadata
    warnings: list[str]
    fat_recovered: bool
    budget: EmbeddedBudget

    @property
    def deadline(self) -> float:
        return self.budget.deadline

    def sources(self) -> AttachmentSources:
        """Datos de adjuntos y cómo abrir un correo adjunto con este mismo flujo."""
        open_message = partial(
            open_embedded_message, self.path, budget=self.budget, read=_read_message
        )
        return AttachmentSources(self.ole.attachments, self.deadline, open_message)

    def fallback_envelope(self) -> list[Envelope]:
        """Respaldos en orden de confianza: propiedades MAPI y luego encabezados de transporte."""
        recovered = self.ole.recovered
        return [envelope_from_properties(recovered), envelope_from_headers(recovered.get("007D"))]

    def finish_attachments(self, attachments: list[AttachmentMetadata]) -> list[AttachmentMetadata]:
        """Suma los adjuntos recuperados de datos sueltos y avisa si alguno tiene advertencias."""
        if self.fat_recovered:
            attachments.extend(raw_recovered_attachments(self.path, self.deadline))
        if any(item.warnings for item in attachments):
            self.warnings.append(_ATTACHMENT_NOTICE)
        return attachments


def extract_msg_file(path: Path, original_name: str, size_bytes: int) -> MessageMetadata:
    """Punto de entrada del análisis: lee el correo y sus correos adjuntos y acota la respuesta."""
    budget = EmbeddedBudget(deadline=time.monotonic() + ATTACHMENT_BUDGET_SECONDS)
    return limit_response(_read_message(path, original_name, size_bytes, budget))


def _read_message(
    path: Path, original_name: str, size_bytes: int, budget: EmbeddedBudget
) -> MessageMetadata:
    """Valida la firma OLE y lee el correo de una copia segura."""
    if not olefile.isOleFile(str(path)):
        raise ExtractionError(
            "El archivo no tiene una firma MSG/OLE válida. Puede estar corrupto "
            "o haber sido renombrado desde otro formato.",
            code="INVALID_OR_CORRUPT_MSG",
        )
    with recovered_ole_path(path) as (read_path, recovery_warnings):
        ole = read_ole_metadata(read_path)
        context = _ReadContext(
            path=read_path,
            original_name=original_name,
            size_bytes=size_bytes,
            ole=ole,
            warnings=filename_warnings(original_name) + recovery_warnings + ole.warnings,
            fat_recovered=bool(recovery_warnings),
            budget=budget,
        )
        try:
            message = extract_msg.openMsg(
                str(read_path), delayAttachments=True, errorBehavior=_PARSER_ERRORS
            )
        except Exception:
            return _recovered_message(context)
        try:
            return _parsed_message(message, context)
        finally:
            try:
                message.close()
            except Exception:
                # El proceso finaliza y el SO libera handles; no perder el resultado recuperado.
                pass


def _recovered_message(context: _ReadContext) -> MessageMetadata:
    """Estrategia de respaldo: correo armado sólo con propiedades OLE legibles."""
    recovered = context.ole.recovered
    if not any(recovered.get(key) for key in _RECOVERABLE_KEYS):
        raise ExtractionError(
            "El contenedor abre, pero no se pudo recuperar contenido del MSG.",
            code="UNREADABLE_MSG",
        ) from None
    context.warnings.append(
        "El lector MSG falló. Se recuperaron propiedades desde OLE y los adjuntos "
        "que permanecen legibles."
    )
    body = best_recovered_body(context.path, recovered.get("1000"), settings.max_body_chars)
    envelope = Envelope().complete_with(*context.fallback_envelope())
    attachments = context.finish_attachments(
        extract_ole_attachments(context.path, context.sources())
    )
    if body.inline and assign_by_size(attachments, body.inline):
        context.warnings.append("Posición de imágenes incrustadas reconstruida por sus medidas.")
    return MessageMetadata(
        file_name=context.original_name,
        file_size_bytes=context.size_bytes,
        subject=envelope.subject,
        sender=envelope.sender,
        recipients=envelope.recipients,
        sent_at=envelope.sent_at,
        body_preview=body.text,
        body_truncated=body.truncated,
        properties=context.ole.items,
        attachments=attachments,
        warnings=context.warnings,
        status="partial",
    )


def _parsed_message(message: object, context: _ReadContext) -> MessageMetadata:
    """Estrategia principal: el parser MSG abrió el correo; cada campo se lee de forma aislada."""
    warnings = context.warnings
    subject = clean_text(read_attribute(message, "subject", warnings))
    sender = clean_text(read_attribute(message, "sender", warnings))
    recipients = read_recipients(message, warnings)
    sent_at = read_attribute(message, "date", warnings)
    if not isinstance(sent_at, datetime):
        sent_at = None
    body = read_body(message, context.ole.recovered, warnings)
    received_at = read_received_at(message, warnings)
    truncated = bool(body and len(body) > settings.max_body_chars)
    if truncated:
        warnings.append(f"Cuerpo largo: se muestran {settings.max_body_chars:,} caracteres.")
    headers, header_date = read_headers(message, warnings, need_date=sent_at is None)
    envelope = Envelope(subject, sender, recipients, sent_at or header_date).complete_with(
        *context.fallback_envelope()
    )
    properties = read_message_properties(message, warnings) + context.ole.items
    properties.extend(read_fixed_properties(message, warnings))
    attachments = context.finish_attachments(
        extract_parsed_attachments(message, warnings, context.sources())
    )
    return MessageMetadata(
        file_name=context.original_name,
        file_size_bytes=context.size_bytes,
        subject=envelope.subject,
        sender=envelope.sender,
        recipients=envelope.recipients,
        sent_at=envelope.sent_at,
        received_at=received_at,
        body_preview=body[: settings.max_body_chars] if body else None,
        body_truncated=truncated,
        properties=properties,
        headers=headers,
        attachments=attachments,
        warnings=warnings,
        status="partial" if warnings else "complete",
    )
