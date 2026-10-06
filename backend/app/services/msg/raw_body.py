"""Recupera el cuerpo HTML original desde un RTF comprimido que sobrevive suelto en el archivo.

Outlook guarda el cuerpo como RTF comprimido (firma ``LZFu``) con el HTML encapsulado. Si la FAT
dañada deja ese stream sin enlace, sus bytes suelen seguir contiguos. Se acepta sólo si:
la descompresión valida su CRC, el RTF encapsula HTML y su texto coincide con el cuerpo legible
(así no se confunde con el RTF de un adjunto u otro mensaje).
"""

import re
from dataclasses import dataclass, field
from pathlib import Path

from app.services.body_text import html_to_text
from app.services.msg.inline_images import InlineTag, inline_tags
from app.services.msg.raw_recovery import signature_offsets

_SIGNATURE = b"LZFu"
_HEADER = 16
_MAX_COMPRESSED = 32 * 1024 * 1024
#: Caracteres iniciales del cuerpo legible que deben aparecer en el texto del HTML recuperado.
_PROBE_LENGTH = 160


def recover_html_body(path: Path, plain_body: str | None) -> str | None:
    """HTML del cuerpo, o ``None`` si no hay un RTF suelto válido y coherente con el texto."""
    for offset in signature_offsets(path, _SIGNATURE):
        html = _html_at(path, offset - 8)
        if html and _matches(html, plain_body):
            return html
    return None


def _html_at(path: Path, start: int) -> str | None:
    if start < 0:
        return None
    with path.open("rb") as source:
        source.seek(start)
        header = source.read(_HEADER)
        if len(header) < _HEADER:
            return None
        compressed_size = int.from_bytes(header[:4], "little")
        if not _HEADER - 4 <= compressed_size <= _MAX_COMPRESSED:
            return None
        source.seek(start)
        blob = source.read(compressed_size + 4)
    try:
        import compressed_rtf
        from RTFDE.deencapsulate import DeEncapsulator

        rtf = compressed_rtf.decompress(blob)  # Lanza si el CRC no coincide.
        if b"fromhtml" not in rtf[:4096]:
            return None
        deencapsulator = DeEncapsulator(rtf)
        deencapsulator.deencapsulate()
        html = deencapsulator.html
        return html.decode("utf-8", errors="replace") if isinstance(html, bytes) else html
    except Exception:
        return None


def _matches(html: str, plain_body: str | None) -> bool:
    """El texto del HTML debe contener el comienzo del cuerpo legible (normalizado)."""
    if not plain_body:
        return True
    probe = _normalized(plain_body)[:_PROBE_LENGTH]
    return bool(probe) and probe in _normalized(html_to_text(html))


def _normalized(text: str) -> str:
    text = re.sub(r"<mailto:[^>]*>", " ", text)
    return re.sub(r"[^0-9a-z]+", " ", text.lower()).strip()


@dataclass(frozen=True)
class RecoveredBody:
    text: str | None
    truncated: bool
    #: Imágenes ``cid`` del HTML recuperado, para reconstruir su posición por medidas.
    inline: list[InlineTag] = field(default_factory=list)


def best_recovered_body(path: Path, plain_body: str | None, max_chars: int) -> RecoveredBody:
    """Cuerpo de un correo cuyo parser falló: el texto legible o, si no marca imágenes o está
    truncado, el HTML original recuperado del RTF suelto (con imágenes en posición)."""
    plain_truncated = bool(plain_body and "[truncado;" in plain_body)
    if plain_body and "[cid:" in plain_body and not plain_truncated:
        return RecoveredBody(plain_body, False)
    html = recover_html_body(path, plain_body)
    if not html:
        return RecoveredBody(plain_body, plain_truncated)
    text = html_to_text(html)
    return RecoveredBody(text[:max_chars] or None, len(text) > max_chars, inline_tags(html))
