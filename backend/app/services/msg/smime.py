"""Correos firmados o cifrados con S/MIME y correos con permisos IRM (PEN-06).

Outlook guarda un correo S/MIME (clase ``IPM.Note.SMIME…``) con un único adjunto ``smime.p7m``:
- Firmado en claro: el adjunto es un MIME ``multipart/signed`` cuya primera parte es el contenido
  (texto y adjuntos reales); se muestra ese contenido. La firma no se verifica aquí.
- Firmado opaco (``opaque``) o cifrado: el adjunto es un PKCS#7 (``signedData`` o
  ``envelopedData``); el contenido no se puede mostrar sin desempaquetarlo o sin la clave. Se avisa
  y el ``.p7m`` se descarga.
Un correo con permisos (IRM) guarda su contenido protegido en ``message.rpmsg``: sólo se avisa.
Análisis y descarga usan ``smime_content``: mismas partes, mismos índices.
"""

from dataclasses import dataclass
from email import policy
from email.message import EmailMessage
from email.parser import BytesParser
from pathlib import Path
from typing import Literal

import olefile

from app.services.msg.attachment_entries import ATTACHMENT_DATA_STREAM, OleAttachment

#: Tipo de contenido PKCS#7 (OID DER) al inicio del ``.p7m``.
_SIGNED_DATA = bytes.fromhex("06092A864886F70D010702")
_ENVELOPED_DATA = bytes.fromhex("06092A864886F70D010703")
_OID_WINDOW = 64
_SMIME_CLASS = ".smime"
_IRM_CLASS = ".rpmsg"
_IRM_ATTACHMENT = "message.rpmsg"


@dataclass(frozen=True)
class SmimeContent:
    security: Literal["signed", "opaque", "encrypted", "protected"]
    #: Contenido firmado legible (firma en claro); ``None`` si es opaco o cifrado.
    content: EmailMessage | None = None


def smime_content(
    path: Path, message_class: str | None, attachments: dict[str, OleAttachment]
) -> SmimeContent | None:
    """Qué es el correo S/MIME o IRM y, si se firmó en claro, su contenido; si no, ``None``."""
    lowered = (message_class or "").lower()
    names = {info.name.lower() for info in attachments.values()}
    if _IRM_CLASS in lowered or _IRM_ATTACHMENT in names:
        return SmimeContent("protected")
    if _SMIME_CLASS not in lowered or len(attachments) != 1:
        return None
    payload = _single_attachment(path, next(iter(attachments)))
    if payload is None:
        return None
    head = payload[:_OID_WINDOW]
    if _ENVELOPED_DATA in head:
        return SmimeContent("encrypted")
    if _SIGNED_DATA in head:
        return SmimeContent("opaque")
    content = _signed_part(payload)
    return SmimeContent("signed", content) if content is not None else SmimeContent("opaque")


def _single_attachment(path: Path, directory: str) -> bytes | None:
    try:
        with olefile.OleFileIO(str(path)) as container:
            stream_path = [directory, ATTACHMENT_DATA_STREAM]
            if not container.exists(stream_path):
                return None
            with container.openstream(stream_path) as stream:
                return stream.read()
    except Exception:
        return None


def _signed_part(payload: bytes) -> EmailMessage | None:
    """Primera parte de un ``multipart/signed``: el contenido que se firmó."""
    try:
        message = BytesParser(policy=policy.default).parsebytes(payload)
    except Exception:
        return None
    if message.get_content_type() != "multipart/signed":
        return None
    parts = list(message.iter_parts())
    return parts[0] if parts else None
