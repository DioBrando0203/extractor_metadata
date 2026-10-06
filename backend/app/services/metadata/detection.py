"""Reconocimiento del formato real de un adjunto por su firma, no por su extensión."""

import mimetypes
import zipfile
from io import BytesIO
from pathlib import Path

from app.services.metadata.results import DetectedFile

CFB_SIGNATURE = bytes.fromhex("D0CF11E0A1B11AE1")


PDF_SIGNATURE = b"%PDF-"


def image_signature(payload: bytes) -> tuple[str, str, str] | None:
    if payload.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image", "image/png", "PNG"
    if payload.startswith(b"\xff\xd8\xff"):
        return "image", "image/jpeg", "JPEG"
    if payload.startswith((b"GIF87a", b"GIF89a")):
        return "image", "image/gif", "GIF"
    if payload.startswith(b"BM"):
        return "image", "image/bmp", "BMP"
    if payload.startswith((b"II*\x00", b"MM\x00*")):
        return "image", "image/tiff", "TIFF"
    if payload.startswith(b"RIFF") and payload[8:12] == b"WEBP":
        return "image", "image/webp", "WebP"
    return None


def zip_kind(payload: bytes) -> tuple[str, str | None, str] | None:
    """Reconoce OOXML leyendo sólo el directorio ZIP, no hojas ni documento."""
    try:
        with zipfile.ZipFile(BytesIO(payload)) as archive:
            names = set(archive.namelist())
    except (OSError, zipfile.BadZipFile):
        return None
    if "xl/workbook.xml" in names:
        return (
            "xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "ZIP/OOXML Excel",
        )
    if "word/document.xml" in names:
        return (
            "docx",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "ZIP/OOXML Word",
        )
    if "ppt/presentation.xml" in names:
        return (
            "pptx",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            "ZIP/OOXML PowerPoint",
        )
    return "zip", "application/zip", "ZIP"


def looks_like_dxf(payload: bytes) -> bool:
    head = payload[:2_048].decode("latin-1", errors="ignore").upper()
    return "SECTION" in head and ("HEADER" in head or "ENTITIES" in head)


def detect_file(payload: bytes, filename: str) -> DetectedFile:
    extension = Path(filename).suffix.lower()
    image = image_signature(payload)
    if image:
        kind, content_type, signature = image
        return DetectedFile(kind, content_type, extension, signature)
    if payload.startswith(PDF_SIGNATURE):
        return DetectedFile("pdf", "application/pdf", extension, "PDF")
    if payload.startswith(CFB_SIGNATURE):
        office_types = {
            ".xls": "application/vnd.ms-excel",
            ".doc": "application/msword",
            ".ppt": "application/vnd.ms-powerpoint",
        }
        return DetectedFile(
            "ole", office_types.get(extension, "application/x-ole-storage"), extension, "OLE/CFB"
        )
    if payload.startswith((b"PK\x03\x04", b"PK\x05\x06")):
        ooxml = zip_kind(payload)
        if ooxml:
            kind, content_type, signature = ooxml
            return DetectedFile(kind, content_type, extension, signature)
    if len(payload) >= 6 and payload[:2] == b"AC" and payload[2:6].isdigit():
        return DetectedFile("dwg", "application/acad", extension, "DWG")
    if extension == ".dxf" or looks_like_dxf(payload):
        return DetectedFile("dxf", "application/dxf", extension, "DXF")
    if extension == ".dwg":
        return DetectedFile(
            "dwg", "application/acad", extension, "Extensión DWG (firma no verificada)"
        )
    return DetectedFile("generic", mimetypes.guess_type(filename)[0], extension, "No reconocida")
