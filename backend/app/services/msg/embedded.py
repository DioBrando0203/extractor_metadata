"""Correos adjuntos (método 5): copia a un MSG independiente y lectura con el mismo flujo.

Un correo adjunto vive en la carpeta ``__substg1.0_3701000D`` de su adjunto. Para leerlo como el
correo principal se copia a un archivo propio, dentro del temporal de la solicitud, con las dos
diferencias que exige el formato (MS-OXMSG): el stream de propiedades raíz lleva 8 bytes reservados
más y las propiedades con nombre (``__nameid_version1.0``) se toman del correo contenedor.
No interpreta el mensaje: recibe de ``reader`` la función que lo lee.
"""

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import olefile
from extract_msg.ole_writer import OleWriter

from app.core.config import settings
from app.core.errors import ExtractionError
from app.models.schemas import AttachmentMetadata, MessageMetadata
from app.services.msg.attachment_entries import (
    EMBEDDED_STORAGE,
    PROPERTIES_STREAM,
    OleAttachment,
)

MESSAGE_CONTENT_TYPE = "application/vnd.ms-outlook"
_NAMEID_STORAGE = "__nameid_version1.0"
#: Encabezado del stream de propiedades: 24 bytes en un mensaje incrustado y 32 en uno raíz.
_EMBEDDED_HEADER = 24
_TOP_LEVEL_RESERVED = b"\0" * 8
_GENERIC_NAME = "adjunto-"


@dataclass
class EmbeddedBudget:
    """Límites que comparten un correo y todos los correos adjuntos que contiene (PY-20)."""

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


#: Lee un MSG ya copiado: ``(ruta, nombre, tamaño, presupuesto) -> MessageMetadata``.
ReadMessage = Callable[[Path, str, int, EmbeddedBudget], MessageMetadata]


@dataclass(frozen=True)
class EmbeddedCopy:
    size: int
    #: Streams que no se pudieron leer en un archivo dañado y quedaron fuera de la copia.
    skipped_streams: int


def message_filename(name: str) -> str:
    """Nombre de un correo adjunto como archivo: su nombre o asunto con extensión ``.msg``."""
    return name if name.lower().endswith(".msg") else f"{name}.msg"


def is_embedded_message(container: olefile.OleFileIO, directory: str) -> bool:
    return bool(container.exists([directory, EMBEDDED_STORAGE, PROPERTIES_STREAM]))


def write_embedded_message(path: Path, directory: str, target: Path) -> EmbeddedCopy:
    """Escribe en ``target`` el correo adjunto de la carpeta ``directory`` como MSG propio.

    Cada stream se copia por separado: uno ilegible de un archivo dañado se omite y se cuenta.
    """
    writer = OleWriter()
    with olefile.OleFileIO(str(path)) as container:
        if not is_embedded_message(container, directory):
            raise ExtractionError(
                "El adjunto solicitado no es un correo.", code="ATTACHMENT_NOT_FOUND"
            )
        skipped = _copy_streams(container, [directory, EMBEDDED_STORAGE], writer)
        _copy_named_properties(container, writer)
    writer.write(str(target))
    return EmbeddedCopy(target.stat().st_size, skipped)


def open_embedded_message(
    path: Path, directory: str, info: OleAttachment, budget: EmbeddedBudget, read: ReadMessage
) -> AttachmentMetadata:
    """Adjunto ``message`` con el correo interno leído, o con un aviso si no se pudo abrir."""
    attachment = AttachmentMetadata(
        name=info.name, kind="message", content_type=MESSAGE_CONTENT_TYPE
    )
    if refusal := budget.refusal():
        attachment.warnings.append(refusal)
        return attachment
    target = path.parent / f"{path.stem}-{directory.rsplit('#', 1)[-1]}.msg"
    budget.opened += 1
    budget.depth += 1
    try:
        copy = write_embedded_message(path, directory, target)
        inner = read(target, message_filename(info.name), copy.size, budget)
        if copy.skipped_streams:
            inner.warnings.append("Parte del correo adjunto estaba dañada y no se pudo leer.")
            inner.status = "partial"
        attachment.message = inner
        attachment.size_bytes = copy.size
        if info.name.startswith(_GENERIC_NAME):
            attachment.name = inner.subject or "Correo adjunto"
    except Exception:
        attachment.warnings.append(
            "No se pudo abrir el correo adjunto; descárgalo para abrirlo con Outlook."
        )
    finally:
        budget.depth -= 1
        target.unlink(missing_ok=True)
    return attachment


def _copy_streams(container: olefile.OleFileIO, root: list[str], writer: OleWriter) -> int:
    skipped = 0
    for parts in container.listdir(streams=True, storages=False):
        if len(parts) <= len(root) or parts[: len(root)] != root:
            continue
        relative = parts[len(root) :]
        try:
            with container.openstream(parts) as stream:
                data = stream.read()
            if relative == [PROPERTIES_STREAM]:
                data = _top_level_properties(data)
            writer.addEntry(relative, data)
        except Exception:
            skipped += 1
    return skipped


def _top_level_properties(data: bytes) -> bytes:
    """Agrega los 8 bytes reservados que un stream de propiedades raíz tiene y uno incrustado no."""
    if len(data) % 16 != _EMBEDDED_HEADER % 16:
        return data
    return data[:_EMBEDDED_HEADER] + _TOP_LEVEL_RESERVED + data[_EMBEDDED_HEADER:]


def _copy_named_properties(container: olefile.OleFileIO, writer: OleWriter) -> None:
    """El correo adjunto usa la tabla de propiedades con nombre del correo que lo contiene."""
    for parts in container.listdir(streams=True, storages=False):
        if len(parts) != 2 or parts[0] != _NAMEID_STORAGE:
            continue
        try:
            with container.openstream(parts) as stream:
                writer.addEntry(parts, stream.read())
        except Exception:
            # Ya existía (correo adjunto no estándar con tabla propia) o es ilegible: se conserva
            # la copia; extract_msg tolera nombres de propiedades ausentes.
            continue
