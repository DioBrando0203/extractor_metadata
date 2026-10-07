"""Correos adjuntos: se leen con el mismo flujo que el correo que los contiene.

Tres formas de llegar: la carpeta ``__substg1.0_3701000D`` de un adjunto (método 5, lo que hace
Outlook al reenviar como adjunto), un archivo ``.msg`` adjunto con sus bytes (lo que hacen otros
clientes) o un ``.eml`` adjunto (``eml``). La carpeta se copia a un MSG propio, dentro del
temporal de la solicitud, con las dos diferencias que exige el formato (MS-OXMSG): el stream de
propiedades raíz lleva 8 bytes reservados más y las propiedades con nombre se toman del
correo contenedor.
No interpreta el mensaje: recibe de ``reader`` la función que lo lee.
"""

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import olefile
from extract_msg.ole_writer import OleWriter

from app.core.errors import ExtractionError
from app.models.schemas import AttachmentMetadata, MessageMetadata
from app.services.msg.attachment_entries import EMBEDDED_STORAGE, PROPERTIES_STREAM, OleAttachment
from app.services.msg.eml import EML_CONTENT_TYPE, looks_like_eml, parse_eml, read_eml
from app.services.msg.names import message_filename
from app.services.msg.nesting import EmbeddedBudget, open_nested

MESSAGE_CONTENT_TYPE = "application/vnd.ms-outlook"
CFB_SIGNATURE = bytes.fromhex("D0CF11E0A1B11AE1")
#: Nombre UTF-16 de los streams MAPI: separa un MSG de otro archivo CFB (.doc, .xls).
_MSG_MARKER = "__substg1.0_".encode("utf-16-le")
_NAMEID_STORAGE = "__nameid_version1.0"
#: Encabezado del stream de propiedades: 24 bytes en un mensaje incrustado y 32 en uno raíz.
_EMBEDDED_HEADER = 24
_TOP_LEVEL_RESERVED = b"\0" * 8
_DAMAGED = "Parte del correo adjunto estaba dañada y no se pudo leer."

#: Lee un MSG ya copiado: ``(ruta, nombre, tamaño, presupuesto) -> MessageMetadata``.
ReadMessage = Callable[[Path, str, int, EmbeddedBudget], MessageMetadata]


@dataclass(frozen=True)
class EmbeddedCopy:
    size: int
    #: Streams que no se pudieron leer en un archivo dañado y quedaron fuera de la copia.
    skipped_streams: int


def is_msg_payload(payload: bytes) -> bool:
    return payload.startswith(CFB_SIGNATURE) and _MSG_MARKER in payload


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


@dataclass(frozen=True)
class AttachedMessages:
    """Abre los correos adjuntos de ``path`` con el flujo que aporta ``reader``."""

    path: Path
    budget: EmbeddedBudget
    read: ReadMessage

    def from_storage(self, directory: str, info: OleAttachment) -> AttachmentMetadata:
        """Correo adjunto guardado como carpeta OLE (método 5)."""
        attachment = AttachmentMetadata(name=info.name, content_type=MESSAGE_CONTENT_TYPE)
        target = self._sibling(directory.rsplit("#", 1)[-1])

        def read() -> MessageMetadata:
            try:
                copy = write_embedded_message(self.path, directory, target)
                attachment.size_bytes = copy.size
                inner = self.read(target, message_filename(info.name), copy.size, self.budget)
            finally:
                target.unlink(missing_ok=True)
            if copy.skipped_streams:
                inner.warnings.append(_DAMAGED)
                inner.status = "partial"
            return inner

        return open_nested(attachment, read, self.budget)

    def from_file(self, attachment: AttachmentMetadata, payload: bytes) -> AttachmentMetadata:
        """Un ``.msg`` o ``.eml`` adjunto como archivo se lee como correo; otro no cambia."""
        if is_msg_payload(payload):
            attachment.content_type = MESSAGE_CONTENT_TYPE
            return open_nested(
                attachment, lambda: self._read_file(attachment.name, payload), self.budget
            )
        message = parse_eml(payload) if looks_like_eml(attachment.name) else None
        if message is None:
            return attachment
        attachment.content_type = EML_CONTENT_TYPE
        size = len(payload)
        return open_nested(
            attachment, lambda: read_eml(message, attachment.name, size, self.budget), self.budget
        )

    def _read_file(self, name: str, payload: bytes) -> MessageMetadata:
        target = self._sibling(f"f{self.budget.opened}")
        try:
            target.write_bytes(payload)
            return self.read(target, message_filename(name), len(payload), self.budget)
        finally:
            target.unlink(missing_ok=True)

    def _sibling(self, tag: str) -> Path:
        return self.path.parent / f"{self.path.stem}-{tag}.msg"


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
