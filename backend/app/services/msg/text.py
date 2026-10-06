"""Conversión defensiva de valores del parser MSG a texto acotado y serializable."""

from datetime import date, datetime
from enum import Enum

from app.core.config import settings


def clean_text(value: object | None, limit: int = settings.max_property_chars) -> str | None:
    if value is None:
        return None
    if isinstance(value, bytes):
        return f"Binario: {len(value):,} bytes (contenido omitido)"
    if isinstance(value, Enum):
        value = value.name
    if isinstance(value, (datetime, date)):
        value = value.isoformat()
    text = str(value).strip()
    if len(text) > limit:
        text = text[:limit] + f" … [truncado; {len(text):,} caracteres]"
    return text or None


def read_attribute(message: object, name: str, warnings: list[str]) -> object | None:
    try:
        return getattr(message, name, None)
    except Exception:
        warnings.append(
            f"No se pudo recuperar la propiedad {name}; se conserva el resto del mensaje."
        )
        return None


def normalize_content_id(value: str | None) -> str | None:
    """Content-ID comparable: sin ``<>``, espacios ni prefijo ``cid:``."""
    if not value:
        return None
    cleaned = value.strip().strip("<>").strip()
    if cleaned.lower().startswith("cid:"):
        cleaned = cleaned[4:]
    return cleaned or None
