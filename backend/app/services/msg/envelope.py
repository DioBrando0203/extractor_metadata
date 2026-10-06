"""Sobre del correo (asunto, remitente, destinatarios y fecha) desde fuentes de respaldo.

Cuando el parser MSG falla o devuelve campos vacíos, estos datos suelen sobrevivir en otras partes
del archivo: propiedades MAPI alternativas o los encabezados de transporte (``007D``), que viven en
sectores normales y resisten daños del mini stream. Todo lo que devuelve este módulo es dato real
del correo, nunca una deducción.
"""

from dataclasses import dataclass, field, fields
from datetime import datetime
from email.header import decode_header, make_header
from email.parser import HeaderParser
from email.utils import getaddresses, parsedate_to_datetime

from app.services.msg.text import clean_text

_RECIPIENT_HEADERS = (("To", "Para"), ("Cc", "CC"), ("Bcc", "CCO"))
_DISPLAY_RECIPIENTS = (("0E04", "Para"), ("0E03", "CC"), ("0E02", "CCO"))


@dataclass
class Envelope:
    subject: str | None = None
    sender: str | None = None
    #: Líneas ``Para: …``, ``CC: …`` y ``CCO: …`` como las arma el parser principal.
    recipients: list[str] = field(default_factory=list)
    sent_at: datetime | None = None

    def complete_with(self, *fallbacks: "Envelope") -> "Envelope":
        """Rellena cada campo vacío con el primer respaldo que lo tenga (cadena de respaldo)."""
        for fallback in fallbacks:
            for item in fields(self):
                if not getattr(self, item.name) and getattr(fallback, item.name):
                    setattr(self, item.name, getattr(fallback, item.name))
        return self


def envelope_from_headers(raw_headers: str | None) -> Envelope:
    """Lee From, To, Cc, Bcc, Subject y Date de los encabezados de transporte del MSG."""
    if not raw_headers:
        return Envelope()
    try:
        headers = HeaderParser().parsestr(raw_headers, headersonly=True)
    except Exception:
        return Envelope()
    envelope = Envelope(
        subject=_decoded(headers.get("Subject")),
        sender=_addresses(headers.get_all("From")),
    )
    for key, label in _RECIPIENT_HEADERS:
        addresses = _addresses(headers.get_all(key))
        if addresses:
            envelope.recipients.append(f"{label}: {addresses}")
    envelope.sent_at = _date(headers.get("Date"))
    return envelope


def envelope_from_properties(recovered: dict[str, str]) -> Envelope:
    """Propiedades MAPI de texto: principales primero y después sus equivalentes alternativos."""
    subject = _first(recovered, "0037")
    if not subject:
        normalized = _first(recovered, "0E1D")
        prefix = _first(recovered, "003D")
        subject = f"{prefix} {normalized}" if prefix and normalized else normalized
    envelope = Envelope(
        subject=subject or _first(recovered, "0070"),
        sender=_sender(recovered),
    )
    for key, label in _DISPLAY_RECIPIENTS:
        value = _first(recovered, key)
        if value:
            envelope.recipients.append(f"{label}: {value}")
    return envelope


def _sender(recovered: dict[str, str]) -> str | None:
    """Nombre y correo del remitente; si falta, el de "enviado en nombre de"."""
    for name_key, email_keys in (("0C1A", ("5D01", "0C1F")), ("0042", ("5D02", "0065"))):
        name = _first(recovered, name_key)
        # Las direcciones Exchange internas (/O=…) no son correos útiles para una persona.
        email = next(
            (_first(recovered, key) for key in email_keys if "@" in (_first(recovered, key) or "")),
            None,
        )
        if name and email and name != email:
            return f"{name} <{email}>"
        if name or email:
            return name or email
    return None


def _first(recovered: dict[str, str], key: str) -> str | None:
    return clean_text(recovered.get(key)) if recovered.get(key) else None


def _decoded(value: str | None) -> str | None:
    """Decodifica palabras codificadas RFC 2047 (``=?utf-8?…?=``)."""
    if not value:
        return None
    try:
        return clean_text(str(make_header(decode_header(value))))
    except Exception:
        return clean_text(value)


def _addresses(values: list[str] | None) -> str | None:
    if not values:
        return None
    parts = []
    for name, email in getaddresses([_decoded(value) or "" for value in values]):
        if name and email:
            parts.append(f"{name} <{email}>")
        elif name or email:
            parts.append(name or email)
    return "; ".join(parts) or None


def _date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return parsedate_to_datetime(value)
    except (TypeError, ValueError, OverflowError):
        return None
