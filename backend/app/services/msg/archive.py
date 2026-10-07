"""Todos los adjuntos de un correo en un ZIP, dentro del temporal de la solicitud (PEN-11).

Recorre los adjuntos en el orden del análisis con la misma fuente que la descarga individual
(``download.open_source``): correo, correo adjunto, contenido firmado o lectura de rescate. Un
adjunto sin bytes (un enlace) o ilegible se omite sin interrumpir el resto; los nombres repetidos
se numeran como lo haría el explorador de archivos.
"""

import zipfile
from pathlib import Path, PurePosixPath

from app.core.errors import ExtractionError
from app.services.msg.download import open_source

ZIP_CONTENT_TYPE = "application/zip"


def extract_all_attachments(
    path: Path, destination: Path, archive_name: str, message_path: tuple[int, ...] = ()
) -> tuple[str, str]:
    """Escribe en ``destination`` un ZIP con los adjuntos descargables; devuelve (nombre, MIME)."""
    source = open_source(path, message_path, destination)
    part = destination.with_name("parte.bin")
    used: set[str] = set()
    try:
        with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for index in range(source.count()):
                try:
                    filename, _ = source.extract(index, part)
                except Exception:
                    continue  # Enlace sin bytes o adjunto ilegible (PY-16): se omite.
                archive.write(part, _unique(filename, used))
    finally:
        part.unlink(missing_ok=True)
    if not used:
        raise ExtractionError(
            "Este correo no tiene adjuntos que se puedan descargar.", code="ATTACHMENT_NOT_FOUND"
        )
    return archive_name, ZIP_CONTENT_TYPE


def _unique(name: str, used: set[str]) -> str:
    """``informe.pdf``, ``informe (2).pdf``…; sin distinguir mayúsculas, como en Windows."""
    stem, suffix = PurePosixPath(name).stem, PurePosixPath(name).suffix
    candidate, number = name, 1
    while candidate.lower() in used:
        number += 1
        candidate = f"{stem} ({number}){suffix}"
    used.add(candidate.lower())
    return candidate
