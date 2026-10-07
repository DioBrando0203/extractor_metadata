"""Lectura de rescate de un MSG cuya cabecera está destruida (PEN-03).

Sin cabecera no hay FAT ni directorio y no se puede recorrer el árbol OLE. Lo que el correo
guardaba en sectores contiguos suele seguir ahí: los adjuntos completos (``raw_recovery``), el
cuerpo como RTF comprimido con CRC (``raw_body``) y los encabezados de transporte en UTF-16, de
donde salen remitente, asunto, destinatarios y fecha. Todo se valida; nada se deduce.
"""

import re
from pathlib import Path
from typing import BinaryIO

from app.core.config import settings
from app.core.errors import ExtractionError
from app.models.schemas import MessageMetadata
from app.services.msg.envelope import envelope_from_headers
from app.services.msg.inline_images import assign_by_size
from app.services.msg.raw_body import best_recovered_body
from app.services.msg.raw_recovery import raw_recovered_attachments, signature_offsets

#: Campos con los que suelen empezar los encabezados de transporte, en UTF-16 como los guarda MAPI.
_HEADER_FIELDS = tuple(
    field.encode("utf-16-le") for field in ("Received: ", "Return-Path: ", "From: ")
)
_MAX_HITS = 64
_MAX_BACK = 64 * 1024
_MAX_FORWARD = 1024 * 1024
_FIRST_HEADER = re.compile(r"^[A-Za-z0-9-]+:", re.MULTILINE)
_RESCUE_NOTICE = (
    "La cabecera del archivo está destruida: se rescataron los datos que siguen enteros "
    "(sobre, texto y adjuntos). Puede faltar parte del correo."
)


def rescue_message(
    path: Path, original_name: str, size_bytes: int, deadline: float
) -> MessageMetadata:
    """Correo armado sólo con datos sueltos validados; error si no queda nada legible."""
    headers = transport_headers(path)
    envelope = envelope_from_headers(headers)
    body = best_recovered_body(path, None, settings.max_body_chars)
    attachments = raw_recovered_attachments(path, deadline)
    if not (envelope.sender or envelope.subject or body.text or attachments):
        raise ExtractionError(
            "El archivo no tiene una firma MSG/OLE válida. Puede estar corrupto "
            "o haber sido renombrado desde otro formato.",
            code="INVALID_OR_CORRUPT_MSG",
        )
    warnings = [_RESCUE_NOTICE]
    if body.inline and assign_by_size(attachments, body.inline):
        warnings.append("Posición de imágenes incrustadas reconstruida por sus medidas.")
    return MessageMetadata(
        file_name=original_name,
        file_size_bytes=size_bytes,
        subject=envelope.subject,
        sender=envelope.sender,
        recipients=envelope.recipients,
        sent_at=envelope.sent_at,
        body_preview=body.text,
        body_truncated=body.truncated,
        attachments=attachments,
        warnings=warnings,
        status="partial",
    )


def transport_headers(path: Path) -> str | None:
    """Primer bloque de texto UTF-16 que se lee como encabezados con remitente o asunto."""
    hits = sorted(offset for field in _HEADER_FIELDS for offset in signature_offsets(path, field))[
        :_MAX_HITS
    ]
    file_size = path.stat().st_size
    with path.open("rb") as source:
        for hit in hits:
            text = _headers_from(_utf16_block(source, hit, file_size))
            envelope = envelope_from_headers(text)
            if text and (envelope.sender or envelope.subject):
                return text
    return None


def _utf16_block(source: BinaryIO, hit: int, file_size: int) -> str:
    """Texto UTF-16 contiguo alrededor de ``hit``: hasta un NUL o un carácter que no es texto."""
    start = max(hit - _MAX_BACK, hit % 2)
    source.seek(start)
    before = source.read(hit - start)
    begin = len(before)
    while begin >= 2 and _is_text(before[begin - 2 : begin]):
        begin -= 2
    source.seek(hit)
    after = source.read(min(_MAX_FORWARD, file_size - hit))
    end = 0
    while end + 2 <= len(after) and _is_text(after[end : end + 2]):
        end += 2
    return (before[begin:] + after[:end]).decode("utf-16-le", errors="replace")


def _is_text(pair: bytes) -> bool:
    code = pair[0] | pair[1] << 8
    return code in (0x09, 0x0A, 0x0D) or (0x20 <= code < 0xD800 and not 0x7F <= code < 0xA0)


def _headers_from(block: str) -> str | None:
    """Recorta lo que precede a la primera línea ``Campo:`` (restos del sector anterior)."""
    match = _FIRST_HEADER.search(block)
    return block[match.start() :] if match else None
