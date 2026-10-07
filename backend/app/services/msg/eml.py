"""Correos EML (``message/rfc822``) adjuntos a un correo.

Se leen con ``email`` de la biblioteca estándar, sin red ni ejecución, al mismo contrato que un MSG:
sobre, texto (el HTML pasa a texto con marcadores ``[cid:…]``) y adjuntos con metadatos y miniatura.
``EmlSource`` recorre las mismas partes, en el mismo orden, para descargarlas.
"""

from collections.abc import Iterator
from dataclasses import dataclass
from email import policy
from email.message import EmailMessage
from email.parser import BytesParser
from pathlib import Path

from app.core.config import settings
from app.core.errors import ExtractionError
from app.models.schemas import AttachmentMetadata, MessageMetadata, MetadataItem
from app.services.body_text import html_to_text
from app.services.msg.attachments import attachment_from_payload
from app.services.msg.names import download_filename, message_filename
from app.services.msg.nesting import EmbeddedBudget, open_nested
from app.services.msg.text import clean_text, normalize_content_id

EML_CONTENT_TYPE = "message/rfc822"
_ENVELOPE = ("from", "subject", "date")
_RECIPIENTS = (("to", "Para"), ("cc", "CC"), ("bcc", "CCO"))
#: Un EML con miles de partes no es un correo legible; las que sobran se ignoran.
_MAX_PARTS = 200
_MAX_HEADERS = 100
_UNREADABLE = "Adjunto ilegible o corrupto: se conserva el resto del mensaje."


def looks_like_eml(name: str) -> bool:
    return name.lower().endswith(".eml")


def parse_eml(payload: bytes) -> EmailMessage | None:
    """El mensaje si los bytes son un correo (tienen De, Asunto o Fecha); si no, ``None``."""
    try:
        message = BytesParser(policy=policy.default).parsebytes(payload)
        return message if any(message.get(header) for header in _ENVELOPE) else None
    except Exception:
        return None


def attachment_parts(message: EmailMessage) -> list[EmailMessage]:
    """Partes que son adjuntos, en el orden del EML: ese orden es el índice de la API."""
    body = {id(part) for part in _body_parts(message)}
    return [part for part in _leaves(message) if id(part) not in body][:_MAX_PARTS]


def read_eml(
    message: EmailMessage, file_name: str, size: int, budget: EmbeddedBudget
) -> MessageMetadata:
    """``MessageMetadata`` de un EML; sus correos adjuntos comparten el presupuesto."""
    body = body_text(message)
    truncated = bool(body and len(body) > settings.max_body_chars)
    attachments = read_parts(message, budget)
    warnings = (
        ["Uno o más adjuntos tienen advertencias."] if any(a.warnings for a in attachments) else []
    )
    date = _header(message, "date")
    return MessageMetadata(
        file_name=file_name,
        file_size_bytes=size,
        subject=clean_text(_header(message, "subject")),
        sender=clean_text(_header(message, "from")),
        recipients=_recipients(message),
        sent_at=getattr(date, "datetime", None),
        body_preview=body[: settings.max_body_chars] if body else None,
        body_truncated=truncated,
        headers=_headers(message),
        attachments=attachments,
        warnings=warnings,
        status="partial" if warnings else "complete",
    )


@dataclass(frozen=True)
class EmlSource:
    """Un EML visto como contenedor de adjuntos para descargarlos con ``message_path``."""

    message: EmailMessage

    def enter(self, index: int, target: Path) -> "EmlSource":
        inner = _inner_message(self._part(index))
        if inner is None:
            raise _not_found()
        return EmlSource(inner)

    def extract(self, index: int, destination: Path) -> tuple[str, str]:
        part = self._part(index)
        name = _part_name(part, index + 1)
        inner = _inner_message(part)
        if inner is not None:
            destination.write_bytes(inner.as_bytes())
            filename, _ = download_filename(message_filename(name, ".eml"), index, b"")
            return filename, EML_CONTENT_TYPE
        payload = part.get_payload(decode=True) or b""
        destination.write_bytes(payload)
        return download_filename(name, index, payload[:32])

    def _part(self, index: int) -> EmailMessage:
        parts = attachment_parts(self.message)
        if not 0 <= index < len(parts):
            raise _not_found()
        return parts[index]


def _not_found() -> ExtractionError:
    return ExtractionError("No se encontró el adjunto solicitado.", code="ATTACHMENT_NOT_FOUND")


def _leaves(message: EmailMessage) -> Iterator[EmailMessage]:
    """Partes finales del árbol MIME; un correo adjunto es una hoja (no se entra en él)."""
    for part in message.iter_parts():
        if part.get_content_type() == EML_CONTENT_TYPE or not part.is_multipart():
            yield part
        else:
            yield from _leaves(part)


def _body_parts(message: EmailMessage) -> list[EmailMessage]:
    candidates = (message.get_body(preferencelist=(kind,)) for kind in ("plain", "html"))
    return [part for part in candidates if part is not None]


def _text(part: EmailMessage | None) -> str | None:
    if part is None:
        return None
    try:
        content = part.get_content()
    except Exception:
        content = (part.get_payload(decode=True) or b"").decode("utf-8", errors="replace")
    return content if isinstance(content, str) and content.strip() else None


def read_parts(message: EmailMessage, budget: EmbeddedBudget) -> list[AttachmentMetadata]:
    """Adjuntos de un mensaje MIME en el orden de ``attachment_parts`` (el índice de la API)."""
    return [
        _attachment(part, position, budget)
        for position, part in enumerate(attachment_parts(message), start=1)
    ]


def body_text(message: EmailMessage) -> str | None:
    """Texto plano, salvo que sólo el HTML marque dónde van las imágenes (como en el MSG)."""
    plain = _text(message.get_body(preferencelist=("plain",)))
    html = _text(message.get_body(preferencelist=("html",)))
    if html and (plain is None or ("cid:" in html and "[cid:" not in plain)):
        return html_to_text(html) or plain
    return plain.strip() if plain else None


def _header(message: EmailMessage, name: str) -> object | None:
    try:
        return message.get(name)
    except Exception:
        return None


def _recipients(message: EmailMessage) -> list[str]:
    lines = []
    for header, label in _RECIPIENTS:
        value = _header(message, header)
        try:
            addresses = [
                f"{item.display_name} <{item.addr_spec}>" if item.display_name else item.addr_spec
                for item in value.addresses
            ]
        except Exception:
            addresses = [str(value)] if value else []
        if addresses:
            lines.append(f"{label}: {'; '.join(addresses)}")
    return lines


def _headers(message: EmailMessage) -> list[MetadataItem]:
    items = []
    for key, value in message.items()[:_MAX_HEADERS]:
        if text := clean_text(str(value)):
            items.append(MetadataItem(group="Encabezado", label=key, value=text))
    return items


def _inner_message(part: EmailMessage) -> EmailMessage | None:
    if part.get_content_type() != EML_CONTENT_TYPE:
        return None
    payload = part.get_payload()
    return payload[0] if isinstance(payload, list) and payload else None


def _part_name(part: EmailMessage, position: int) -> str:
    try:
        name = part.get_filename()
    except Exception:
        name = None
    return clean_text(name) or f"adjunto-{position}"


def _attachment(part: EmailMessage, position: int, budget: EmbeddedBudget) -> AttachmentMetadata:
    name = _part_name(part, position)
    inner = _inner_message(part)
    if inner is not None:
        size = len(inner.as_bytes())
        attachment = AttachmentMetadata(name=name, content_type=EML_CONTENT_TYPE, size_bytes=size)
        file_name = message_filename(name, ".eml")
        return open_nested(attachment, lambda: read_eml(inner, file_name, size, budget), budget)
    try:
        payload = part.get_payload(decode=True) or b""
        content_id = normalize_content_id(clean_text(part.get("content-id")))
        return attachment_from_payload(name, payload, budget.deadline, content_id=content_id)
    except Exception:
        return AttachmentMetadata(name=name, warnings=[_UNREADABLE])
