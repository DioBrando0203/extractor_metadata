"""Nombres de archivo: avisos para el usuario y nombres seguros para descargar adjuntos."""

import mimetypes
import re
from pathlib import Path

INVALID_NAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


RESERVED_NAME = re.compile(r"^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\.|$)", re.I)


def filename_warnings(filename: str) -> list[str]:
    warnings: list[str] = []
    if (
        INVALID_NAME_CHARS.search(filename)
        or RESERVED_NAME.match(filename)
        or filename.rstrip(". ") != filename
    ):
        warnings.append(
            "El nombre puede ser incompatible con Windows. Este análisis usa una "
            "copia temporal de nombre corto; para Outlook pruebe renombrar el original."
        )
    if len(filename) > 150:
        warnings.append("Nombre muy largo: puede superar límites de ruta al abrirlo en Windows.")
    return warnings


def download_filename(name: str, index: int, header: bytes) -> tuple[str, str]:
    """Devuelve un nombre seguro para un adjunto cuyo nombre MAPI puede faltar."""
    filename = INVALID_NAME_CHARS.sub("_", Path(name).name).strip(". ") or f"adjunto-{index + 1}"
    content_type = mimetypes.guess_type(filename)[0]
    if Path(filename).suffix:
        return filename, content_type or "application/octet-stream"
    signatures = (
        (b"\xff\xd8\xff", ".jpg", "image/jpeg"),
        (b"\x89PNG\r\n\x1a\n", ".png", "image/png"),
        (b"%PDF-", ".pdf", "application/pdf"),
    )
    for signature, extension, detected_type in signatures:
        if header.startswith(signature):
            return f"{filename}{extension}", detected_type
    return filename, "application/octet-stream"
