"""Convierte imágenes y miniaturas incrustadas en JPEG acotados para el lector.

Sólo se decodifican formatos de una lista cerrada (sin EPS/PS, que invocarían Ghostscript).
"""

import base64
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Literal

from app.core.errors import ExtractionError
from app.services.previews.embedded import embedded_thumbnail

THUMBNAIL_SIZE = 480


LARGE_PREVIEW_SIZE = 2048


MAX_PREVIEW_SOURCE_BYTES = 64 * 1024 * 1024


MAX_PREVIEW_PIXELS = 100_000_000


JPEG_QUALITY = 82


_ALLOWED_FORMATS = ("PNG", "JPEG", "GIF", "BMP", "DIB", "TIFF", "WEBP", "ICO", "WMF")


_IMAGE_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".jfif",
    ".gif",
    ".bmp",
    ".dib",
    ".tif",
    ".tiff",
    ".webp",
    ".ico",
    ".emf",
    ".wmf",
}


_IMAGE_SIGNATURES = (
    b"\x89PNG\r\n\x1a\n",
    b"\xff\xd8\xff",
    b"GIF87a",
    b"GIF89a",
    b"BM",
    b"II*\x00",
    b"MM\x00*",
)


PreviewSource = Literal["image", "embedded"]


@dataclass(frozen=True)
class Preview:
    jpeg: bytes
    source: PreviewSource


def _is_image(payload: bytes, filename: str) -> bool:
    return (
        payload.startswith(_IMAGE_SIGNATURES)
        or (payload[:4] == b"RIFF" and payload[8:12] == b"WEBP")
        or Path(filename).suffix.lower() in _IMAGE_EXTENSIONS
    )


def _to_jpeg(data: bytes, max_size: int) -> bytes | None:
    try:
        from PIL import Image, ImageOps

        with Image.open(BytesIO(data), formats=_ALLOWED_FORMATS) as source:
            if source.width * source.height > MAX_PREVIEW_PIXELS:
                return None
            source.draft("RGB", (max_size, max_size))  # JPEG: decodifica ya reducido.
            image = ImageOps.exif_transpose(source) or source
            image.thumbnail((max_size, max_size))
            if image.mode in ("RGBA", "LA", "P", "PA"):
                rgba = image.convert("RGBA")
                image = Image.new("RGB", rgba.size, "white")
                image.paste(rgba, mask=rgba.getchannel("A"))
            elif image.mode != "RGB":
                image = image.convert("RGB")
            output = BytesIO()
            image.save(output, "JPEG", quality=JPEG_QUALITY, optimize=True)
            return output.getvalue()
    except Exception:
        # Imagen dañada, formato no soportado en este sistema o bomba de descompresión.
        return None


def render_preview(payload: bytes, filename: str, *, max_size: int) -> Preview | None:
    """Devuelve una vista previa JPEG o ``None``; nunca lanza por un adjunto ilegible."""
    if not payload or len(payload) > MAX_PREVIEW_SOURCE_BYTES:
        return None
    embedded = embedded_thumbnail(payload, filename)
    if embedded is not None:
        jpeg = _to_jpeg(embedded, max_size)
        return Preview(jpeg, "embedded") if jpeg else None
    if not _is_image(payload, filename):
        return None
    jpeg = _to_jpeg(payload, max_size)
    return Preview(jpeg, "image") if jpeg else None


def thumbnail_data_uri(payload: bytes, filename: str) -> tuple[str | None, PreviewSource | None]:
    """Miniatura pequeña embebida en la respuesta JSON del análisis."""
    preview = render_preview(payload, filename, max_size=THUMBNAIL_SIZE)
    if preview is None:
        return None, None
    encoded = base64.b64encode(preview.jpeg).decode("ascii")
    return f"data:image/jpeg;base64,{encoded}", preview.source


def write_large_preview(destination: Path, filename: str) -> tuple[str, str]:
    """Sustituye el adjunto extraído en ``destination`` por su vista previa JPEG grande."""
    rendered = render_preview(destination.read_bytes(), filename, max_size=LARGE_PREVIEW_SIZE)
    if rendered is None:
        raise ExtractionError("Este adjunto no tiene vista previa disponible.", code="NO_PREVIEW")
    destination.write_bytes(rendered.jpeg)
    return f"{Path(filename).stem}-vista-previa.jpg", "image/jpeg"
