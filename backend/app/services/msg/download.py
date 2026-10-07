"""Materializa un único adjunto en un temporal de la solicitud para entregarlo como descarga.

``message_path`` recorre correos adjuntos: ``(2, 0)`` es el adjunto 0 del correo adjunto 0 del
correo adjunto en la posición 2. Cada nivel es un MSG (``_MsgSource``, copiado junto a
``destination``) o un EML (``eml.EmlSource``); ambos entregan sus adjuntos en el orden del análisis.
"""

from dataclasses import dataclass
from functools import cached_property
from pathlib import Path

import olefile

from app.core.errors import ExtractionError
from app.services.msg.attachment_entries import ATTACHMENT_DATA_STREAM, attachment_directories
from app.services.msg.embedded import (
    MESSAGE_CONTENT_TYPE,
    is_embedded_message,
    is_msg_payload,
    write_embedded_message,
)
from app.services.msg.eml import EmlSource, looks_like_eml, parse_eml
from app.services.msg.fat_recovery import readable_container, recovered_ole_path
from app.services.msg.names import download_filename, message_filename
from app.services.msg.ole_reader import read_ole_metadata
from app.services.msg.raw_recovery import loose_candidates
from app.services.msg.reader import parser_fails
from app.services.msg.smime import smime_content

_CHUNK = 1024 * 1024


def extract_attachment_file(
    path: Path, attachment_index: int, destination: Path, message_path: tuple[int, ...] = ()
) -> tuple[str, str]:
    """Copia el adjunto ``attachment_index`` a ``destination``; devuelve (nombre, tipo MIME).

    Los índices siguen el orden de la respuesta de análisis: primero los adjuntos OLE y después
    los recuperados de datos sueltos cuando hubo recuperación de FAT.
    """
    if attachment_index < 0:
        raise _not_found()
    try:
        return open_source(path, message_path, destination).extract(attachment_index, destination)
    except ExtractionError:
        raise
    except Exception as error:
        raise ExtractionError(
            "No fue posible preparar el adjunto para descargar.", code="UNREADABLE_ATTACHMENT"
        ) from error


def open_source(
    path: Path, message_path: tuple[int, ...], scratch: Path
) -> "_MsgSource | EmlSource | _RescueSource":
    """El correo (o correo adjunto) cuyos adjuntos se piden; las copias van junto a ``scratch``."""
    if not readable_container(path):
        # Lectura de rescate (``rescue``): los únicos adjuntos son los archivos sueltos.
        if message_path:
            raise _not_found()
        return _RescueSource(path)
    source: _MsgSource | EmlSource = _MsgSource(path)
    for level, index in enumerate(message_path):
        source = source.enter(index, scratch.with_name(f"embedded-{level}.msg"))
    return source


def _not_found() -> ExtractionError:
    return ExtractionError("No se encontró el adjunto solicitado.", code="ATTACHMENT_NOT_FOUND")


@dataclass(frozen=True)
class _MsgSource:
    """Un MSG en disco visto como contenedor de adjuntos."""

    path: Path

    def enter(self, index: int, target: Path) -> "_MsgSource | EmlSource":
        """Abre el correo adjunto ``index``: carpeta OLE, ``.msg`` o ``.eml`` adjunto."""
        if (signed := self._signed) is not None:
            return signed.enter(index, target)
        with recovered_ole_path(self.path) as (read_path, _):
            directory, name = _directory_at(read_path, index)
            with olefile.OleFileIO(str(read_path)) as container:
                stored = is_embedded_message(container, directory)
                payload = None if stored else _read_data(container, directory)
            if stored:
                write_embedded_message(read_path, directory, target)
                return _MsgSource(target)
        if payload is not None and is_msg_payload(payload):
            target.write_bytes(payload)
            return _MsgSource(target)
        message = parse_eml(payload) if payload is not None and looks_like_eml(name) else None
        if message is None:
            raise _not_found()
        return EmlSource(message)

    def extract(self, index: int, destination: Path) -> tuple[str, str]:
        if (signed := self._signed) is not None:
            return signed.extract(index, destination)
        with recovered_ole_path(self.path) as (read_path, _):
            with olefile.OleFileIO(str(read_path)) as container:
                directories = attachment_directories(container.listdir())
            if index < len(directories):
                directory, name = _directory_at(read_path, index)
                return _copy_ole_attachment(read_path, directory, name, index, destination)
            raw_index = index - len(directories)
            return _copy_raw_attachment(read_path, raw_index, self._has_loose, destination)

    def count(self) -> int:
        """Cuántos adjuntos lista el análisis de este correo, en el mismo orden."""
        if (signed := self._signed) is not None:
            return signed.count()
        with recovered_ole_path(self.path) as (read_path, _):
            with olefile.OleFileIO(str(read_path)) as container:
                total = len(attachment_directories(container.listdir()))
            if self._has_loose:
                total += len(loose_candidates(read_path))
        return total

    @cached_property
    def _has_loose(self) -> bool:
        """Mismo criterio que el análisis: hay archivos sueltos si se reparó o el parser falla."""
        with recovered_ole_path(self.path) as (read_path, recovery_warnings):
            return bool(recovery_warnings) or parser_fails(read_path)

    @cached_property
    def _signed(self) -> EmlSource | None:
        """Firmado en claro: sus adjuntos son los del contenido firmado, como en el análisis."""
        with recovered_ole_path(self.path) as (read_path, _):
            ole = read_ole_metadata(read_path)
            smime = smime_content(read_path, ole.recovered.get("001A"), ole.attachments)
        return EmlSource(smime.content) if smime and smime.content is not None else None


@dataclass(frozen=True)
class _RescueSource:
    """Archivo sin cabecera legible: sus adjuntos son los archivos sueltos rescatados."""

    path: Path

    def extract(self, index: int, destination: Path) -> tuple[str, str]:
        return _copy_raw_attachment(self.path, index, True, destination)

    def count(self) -> int:
        return len(loose_candidates(self.path))


def _directory_at(path: Path, index: int) -> tuple[str, str]:
    """Carpeta OLE del adjunto ``index`` y su nombre, como en el análisis."""
    with olefile.OleFileIO(str(path)) as container:
        directories = attachment_directories(container.listdir())
    if not 0 <= index < len(directories):
        raise _not_found()
    entry = read_ole_metadata(path).attachments.get(directories[index])
    return directories[index], entry.name if entry else f"adjunto-{index + 1}"


def _read_data(container: olefile.OleFileIO, directory: str) -> bytes | None:
    stream_path = [directory, ATTACHMENT_DATA_STREAM]
    if not container.exists(stream_path):
        return None
    with container.openstream(stream_path) as stream:
        return stream.read()


def _copy_ole_attachment(
    path: Path, directory: str, name: str, index: int, destination: Path
) -> tuple[str, str]:
    with olefile.OleFileIO(str(path)) as container:
        stream_path = [directory, ATTACHMENT_DATA_STREAM]
        if container.exists(stream_path):
            return _copy_stream(container, stream_path, name, index, destination)
        is_message = is_embedded_message(container, directory)
    if is_message:
        write_embedded_message(path, directory, destination)
        filename, _ = download_filename(message_filename(name), index, b"")
        return filename, MESSAGE_CONTENT_TYPE
    raise ExtractionError(
        "El adjunto no contiene un archivo que se pueda descargar.",
        code="UNREADABLE_ATTACHMENT",
    )


def _copy_stream(
    container: olefile.OleFileIO, stream_path: list[str], name: str, index: int, destination: Path
) -> tuple[str, str]:
    with container.openstream(stream_path) as source:
        header = source.read(32)
        filename, content_type = download_filename(name, index, header)
        with destination.open("wb") as output:
            output.write(header)
            while chunk := source.read(_CHUNK):
                output.write(chunk)
    return filename, content_type


def _copy_raw_attachment(
    path: Path, raw_index: int, rescue: bool, destination: Path
) -> tuple[str, str]:
    candidates = loose_candidates(path) if rescue else []
    if raw_index < 0 or raw_index >= len(candidates):
        raise _not_found()
    candidate = candidates[raw_index]
    with path.open("rb") as source, destination.open("wb") as output:
        source.seek(candidate.offset)
        remaining = candidate.size
        while remaining:
            chunk = source.read(min(_CHUNK, remaining))
            if not chunk:
                raise ExtractionError(
                    "El adjunto recuperado está incompleto.", code="UNREADABLE_ATTACHMENT"
                )
            output.write(chunk)
            remaining -= len(chunk)
    return candidate.name, candidate.content_type
