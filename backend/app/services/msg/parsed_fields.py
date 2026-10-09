"""Lectura aislada de cada campo del parser MSG: un fallo en uno no afecta a los demás.

Cada función recibe el objeto de ``extract_msg`` y la lista de avisos, y devuelve un valor neutro
si el campo no se puede leer (PY-16, PY-17).
"""

from datetime import datetime
from email.utils import parsedate_to_datetime
from itertools import islice

from app.core.config import settings
from app.models.schemas import MetadataItem
from app.services.body_text import html_to_text
from app.services.msg.inline_images import InlineTag, inline_tags
from app.services.msg.text import clean_text, read_attribute

_RECIPIENT_FIELDS = (("to", "Para"), ("cc", "CC"), ("bcc", "CCO"))


_MESSAGE_FIELDS = (
    ("classType", "Clase"),
    ("importance", "Importancia"),
    ("stringEncoding", "Codificación"),
    ("messageId", "Message-ID"),
)


def read_recipients(message: object, warnings: list[str]) -> list[str]:
    """Líneas ``Para: …``, ``CC: …`` y ``CCO: …`` que el frontend agrupa."""
    recipients = []
    for key, label in _RECIPIENT_FIELDS:
        value = clean_text(read_attribute(message, key, warnings))
        if value:
            recipients.append(f"{label}: {value}")
    return recipients


def read_body(message: object, recovered: dict[str, str], warnings: list[str]) -> str | None:
    """Texto plano; si falta, HTML convertido a texto; si falta, el stream recuperado por OLE.

    Si el texto plano no marca dónde van las imágenes incrustadas pero el HTML sí, se usa el HTML
    convertido: conserva sus ``[cid:…]`` en posición.
    """
    raw = read_attribute(message, "body", warnings)
    body = str(raw) if raw else None
    if body and "[cid:" not in body:
        body = _html_with_inline_images(message) or body
    if not body:
        html = read_attribute(message, "htmlBody", warnings)
        if isinstance(html, (bytes, str)) and html:
            body = html_to_text(html)
    if not body and recovered.get("1000"):
        body = recovered["1000"]
    return body


def read_inline_tags(message: object) -> list[InlineTag]:
    """Imágenes ``cid`` del HTML con sus medidas, para ubicar las rescatadas sin Content-ID."""
    html = read_attribute(message, "htmlBody", [])
    if isinstance(html, bytes):
        html = html.decode("utf-8", errors="replace")
    return inline_tags(html) if isinstance(html, str) else []


def _html_with_inline_images(message: object) -> str | None:
    """HTML convertido a texto sólo si referencia imágenes incrustadas. Sin avisos: es opcional."""
    html = read_attribute(message, "htmlBody", [])
    if isinstance(html, str):
        html = html.encode("utf-8", errors="replace")
    if not isinstance(html, bytes) or b"cid:" not in html.lower():
        return None
    return html_to_text(html) or None


def read_received_at(message: object, warnings: list[str]) -> datetime | None:
    try:
        value = message.props.getValue("0E060040")
    except Exception:
        warnings.append("No se pudo recuperar la fecha de recepción.")
        return None
    return value if isinstance(value, datetime) else None


def read_headers(
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


def read_message_properties(message: object, warnings: list[str]) -> list[MetadataItem]:
    found = []
    for key, label in _MESSAGE_FIELDS:
        value = clean_text(read_attribute(message, key, warnings))
        if value:
            found.append(MetadataItem(group="Mensaje", label=label, value=value))
    # Orden histórico de la respuesta: el último campo leído aparece primero.
    return found[::-1]


def read_fixed_properties(message: object, warnings: list[str]) -> list[MetadataItem]:
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
