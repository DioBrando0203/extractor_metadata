"""Materializa un único adjunto en un temporal de la solicitud para entregarlo como descarga.

``message_path`` recorre correos adjuntos: ``(2, 0)`` es el adjunto 0 del correo adjunto 0 del
correo adjunto en la posición 2. Cada nivel se copia a un MSG propio junto a ``destination``.
"""

from pathlib import Path

import olefile

from app.core.errors import ExtractionError
from app.services.msg.attachment_entries import ATTACHMENT_DATA_STREAM, attachment_directories
from app.services.msg.embedded import (
    MESSAGE_CONTENT_TYPE,
    is_embedded_message,
    message_filename,
    write_embedded_message,
)
from app.services.msg.fat_recovery import recovered_ole_path
from app.services.msg.names import download_filename
from app.services.msg.ole_reader import read_ole_metadata
from app.services.msg.raw_recovery import ole_attachment_digests, raw_attachment_candidates

_CHUNK = 1024 * 1024


def extract_attachment_file(
    path: Path, attachment_index: int, destination: Path, message_path: tuple[int, ...] = ()
) -> tuple[str, str]:
    """Copia el adjunto ``attachment_index`` a ``destination``; devuelve (nombre, tipo MIME).

    Los índices siguen el orden de la respuesta de análisis: primero los adjuntos OLE y después
    los recuperados de datos sueltos cuando hubo recuperación de FAT.
    """
    if attachment_index < 0 or not olefile.isOleFile(str(path)):
        raise _not_found()
    for level, index in enumerate(message_path):
        path = _enter_message(path, index, destination.with_name(f"embedded-{level}.msg"))
    with recovered_ole_path(path) as (read_path, recovery_warnings):
        names = read_ole_metadata(read_path).attachments
        try:
            with olefile.OleFileIO(str(read_path)) as container:
                directories = attachment_directories(container.listdir())
            if attachment_index < len(directories):
                directory = directories[attachment_index]
                entry = names.get(directory)
                name = entry.name if entry else f"adjunto-{attachment_index + 1}"
                return _copy_ole_attachment(
                    read_path, directory, name, attachment_index, destination
                )
            raw_index = attachment_index - len(directories)
            return _copy_raw_attachment(read_path, raw_index, bool(recovery_warnings), destination)
        except ExtractionError:
            raise
        except Exception as error:
            raise ExtractionError(
                "No fue posible preparar el adjunto para descargar.", code="UNREADABLE_ATTACHMENT"
            ) from error


def _not_found() -> ExtractionError:
    return ExtractionError("No se encontró el adjunto solicitado.", code="ATTACHMENT_NOT_FOUND")


def _enter_message(path: Path, index: int, target: Path) -> Path:
    """Copia el correo adjunto ``index`` de ``path`` a ``target`` y devuelve su ruta."""
    with recovered_ole_path(path) as (read_path, _):
        with olefile.OleFileIO(str(read_path)) as container:
            directories = attachment_directories(container.listdir())
        if not 0 <= index < len(directories):
            raise _not_found()
        write_embedded_message(read_path, directories[index], target)
    return target


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
    path: Path, raw_index: int, fat_recovered: bool, destination: Path
) -> tuple[str, str]:
    candidates = (
        raw_attachment_candidates(path, ole_attachment_digests(path)) if fat_recovered else []
    )
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
