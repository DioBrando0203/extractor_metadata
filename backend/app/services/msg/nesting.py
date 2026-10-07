"""Presupuesto y apertura de correos adjuntos, comunes a MSG y EML (PY-20).

Un correo adjunto puede contener otros: el presupuesto se comparte en todo el árbol y limita su
profundidad y cuántos se abren por análisis, para que un archivo anidado sin fin no agote el plazo.
"""

from collections.abc import Callable
from dataclasses import dataclass

from app.core.config import settings
from app.models.schemas import AttachmentMetadata, MessageMetadata

_GENERIC_NAME = "adjunto-"
_UNOPENED = "No se pudo abrir el correo adjunto; descárgalo para abrirlo aparte."


@dataclass
class EmbeddedBudget:
    """Límites que comparten un correo y todos los correos adjuntos que contiene."""

    deadline: float
    depth: int = 0
    opened: int = 0

    def refusal(self) -> str | None:
        """Motivo para no abrir otro correo adjunto, o ``None`` si queda presupuesto."""
        if self.depth >= settings.max_embedded_depth:
            return "Correo adjunto con demasiados niveles: descárgalo para abrirlo aparte."
        if self.opened >= settings.max_embedded_messages:
            return "Hay demasiados correos adjuntos: descarga este para abrirlo aparte."
        return None


def open_nested(
    attachment: AttachmentMetadata, read: Callable[[], MessageMetadata], budget: EmbeddedBudget
) -> AttachmentMetadata:
    """Marca el adjunto como correo y lo lee con ``read`` si queda presupuesto.

    Sin presupuesto o ilegible, queda como correo sin leer y con un aviso: se puede descargar.
    """
    attachment.kind = "message"
    if refusal := budget.refusal():
        attachment.warnings.append(refusal)
        return attachment
    budget.opened += 1
    budget.depth += 1
    try:
        attachment.message = read()
    except Exception:
        attachment.warnings.append(_UNOPENED)
    finally:
        budget.depth -= 1
    if attachment.message and attachment.name.startswith(_GENERIC_NAME):
        attachment.name = attachment.message.subject or "Correo adjunto"
    return attachment
