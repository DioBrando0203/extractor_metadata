"""Orquesta la lectura de un MSG con dos estrategias.

1. Parser ``extract_msg``: lectura completa (remitente, destinatarios, fechas, cuerpo, adjuntos).
2. Recuperación OLE: si el parser falla, se arma el correo con lo que el contenedor aún conserva.

Ambas comparten un ``_ReadContext`` y terminan en ``limit_response`` para acotar la respuesta.
"""

import time
from dataclasses import dataclass
from datetime import datetime
from email.utils import parsedate_to_datetime
from itertools import islice
from pathlib import Path

import extract_msg
import olefile
from extract_msg.enums import ErrorBehavior

from app.core.config import settings
from app.core.errors import ExtractionError
from app.models.schemas import AttachmentMetadata, MessageMetadata, MetadataItem
from app.services.body_text import html_to_text
from app.services.msg.attachments import extract_ole_attachments, extract_parsed_attachments
from app.services.msg.fat_recovery import recovered_ole_path
from app.services.msg.limits import limit_response
from app.services.msg.names import filename_warnings
from app.services.msg.ole_reader import OleMetadata, read_ole_metadata
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
#: Propiedades MAPI que justifican devolver un correo recuperado: asunto, cuerpo y remitente.
_RECOVERABLE_KEYS = ("0037", "1000", "0C1A", "0C1F")
_RECIPIENT_FIELDS = (("to", "Para"), ("cc", "CC"), ("bcc", "CCO"))
_MESSAGE_FIELDS = (
    ("classType", "Clase"),
    ("importance", "Importancia"),
    ("stringEncoding", "Codificación"),
    ("messageId", "Message-ID"),
)
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
    deadline: float

    def finish_attachments(self, attachments: list[AttachmentMetadata]) -> list[AttachmentMetadata]:
        """Suma los adjuntos recuperados de datos sueltos y avisa si alguno tiene advertencias."""
        if self.fat_recovered:
            attachments.extend(raw_recovered_attachments(self.path, self.deadline))
        if any(item.warnings for item in attachments):
            self.warnings.append(_ATTACHMENT_NOTICE)
        return attachments


def extract_msg_file(path: Path, original_name: str, size_bytes: int) -> MessageMetadata:
    """Punto de entrada del análisis: valida la firma OLE y lee el correo de una copia segura."""
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
            deadline=time.monotonic() + ATTACHMENT_BUDGET_SECONDS,
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
    body = recovered.get("1000")
    attachments = context.finish_attachments(
        extract_ole_attachments(context.path, context.ole.attachments, context.deadline)
    )
    return limit_response(
        MessageMetadata(
            file_name=context.original_name,
            file_size_bytes=context.size_bytes,
            subject=recovered.get("0037"),
            sender=recovered.get("0C1F") or recovered.get("0C1A"),
            recipients=[recovered["0E04"]] if recovered.get("0E04") else [],
            body_preview=body,
            body_truncated=bool(body and "[truncado;" in body),
            properties=context.ole.items,
            attachments=attachments,
            warnings=context.warnings,
            status="partial",
        )
    )


def _parsed_message(message: object, context: _ReadContext) -> MessageMetadata:
    """Estrategia principal: el parser MSG abrió el correo; cada campo se lee de forma aislada."""
    warnings = context.warnings
    subject = clean_text(read_attribute(message, "subject", warnings))
    sender = clean_text(read_attribute(message, "sender", warnings))
    recipients = _recipients(message, warnings)
    sent_at = read_attribute(message, "date", warnings)
    if not isinstance(sent_at, datetime):
        sent_at = None
    body = _body(message, context.ole.recovered, warnings)
    received_at = _received_at(message, warnings)
    truncated = bool(body and len(body) > settings.max_body_chars)
    if truncated:
        warnings.append(f"Cuerpo largo: se muestran {settings.max_body_chars:,} caracteres.")
    headers, header_date = _headers(message, warnings, need_date=sent_at is None)
    properties = _message_properties(message, warnings) + context.ole.items
    properties.extend(_fixed_properties(message, warnings))
    attachments = context.finish_attachments(
        extract_parsed_attachments(message, warnings, context.ole.attachments, context.deadline)
    )
    return limit_response(
        MessageMetadata(
            file_name=context.original_name,
            file_size_bytes=context.size_bytes,
            subject=subject,
            sender=sender,
            recipients=recipients,
            sent_at=sent_at or header_date,
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


def _recipients(message: object, warnings: list[str]) -> list[str]:
    """Líneas ``Para: …``, ``CC: …`` y ``CCO: …`` que el frontend agrupa."""
    recipients = []
    for key, label in _RECIPIENT_FIELDS:
        value = clean_text(read_attribute(message, key, warnings))
        if value:
            recipients.append(f"{label}: {value}")
    return recipients


def _body(message: object, recovered: dict[str, str], warnings: list[str]) -> str | None:
    """Texto plano; si falta, HTML convertido a texto; si falta, el stream recuperado por OLE."""
    raw = read_attribute(message, "body", warnings)
    body = str(raw) if raw else None
    if not body:
        html = read_attribute(message, "htmlBody", warnings)
        if isinstance(html, (bytes, str)) and html:
            body = html_to_text(html)
    if not body and recovered.get("1000"):
        body = recovered["1000"]
    return body


def _received_at(message: object, warnings: list[str]) -> datetime | None:
    try:
        value = message.props.getValue("0E060040")
    except Exception:
        warnings.append("No se pudo recuperar la fecha de recepción.")
        return None
    return value if isinstance(value, datetime) else None


def _headers(
    message: object, warnings: list[str], *, need_date: bool
) -> tuple[list[MetadataItem], datetime | None]:
    """Encabezados de transporte y, si el parser no dio fecha, la del encabezado ``Date``."""
    header = read_attribute(message, "header", warnings)
    if header is None:
        return [], None
    try:
        items = [
            MetadataItem(group="Encabezado", label=key, value=clean_text(value) or "")
            for key, value in list(header.items())[: settings.max_properties]
        ]
    except Exception:
        warnings.append("Encabezados de transporte parcialmente ilegibles.")
        return [], None
    if not need_date:
        return items, None
    try:
        raw_date = header.get("Date")
        return items, parsedate_to_datetime(raw_date) if raw_date else None
    except (TypeError, ValueError, OverflowError):
        return items, None
    except Exception:
        warnings.append("Encabezados de transporte parcialmente ilegibles.")
        return items, None


def _message_properties(message: object, warnings: list[str]) -> list[MetadataItem]:
    found = []
    for key, label in _MESSAGE_FIELDS:
        value = clean_text(read_attribute(message, key, warnings))
        if value:
            found.append(MetadataItem(group="Mensaje", label=label, value=value))
    # Orden histórico de la respuesta: el último campo leído aparece primero.
    return found[::-1]


def _fixed_properties(message: object, warnings: list[str]) -> list[MetadataItem]:
    result: list[MetadataItem] = []
    store = read_attribute(message, "props", warnings)
    if store is None:
        return result
    try:
        for tag, prop in islice(store.items(), settings.max_properties):
            # Los valores variables ya se muestran desde sus streams OLE.
            if hasattr(prop, "value"):
                value = clean_text(prop.value)
                if value is not None:
                    result.append(
                        MetadataItem(group="Propiedades MAPI", label=f"0x{tag}", value=value)
                    )
    except Exception:
        warnings.append("Algunas propiedades MAPI fijas no pudieron leerse.")
    return result
