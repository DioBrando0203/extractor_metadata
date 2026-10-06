"""Metadatos de imágenes con Pillow: formato, dimensiones y EXIF, sin decodificar píxeles."""

from io import BytesIO

from app.services.metadata.results import DetectedFile, ExtractionResult, add_item, limited


def image_metadata(payload: bytes, _: DetectedFile) -> ExtractionResult:
    result = ExtractionResult()
    try:
        from PIL import ExifTags, Image

        with Image.open(BytesIO(payload)) as image:
            add_item(result, "Imagen", "Formato", image.format or "Desconocido")
            add_item(result, "Imagen", "Dimensiones", f"{image.width} × {image.height}")
            add_item(result, "Imagen", "Modo", image.mode)
            # Sólo se lee el directorio EXIF; no se decodifican los píxeles.
            for tag, value in image.getexif().items():
                add_item(result, "EXIF", str(ExifTags.TAGS.get(tag, f"Etiqueta {tag}")), value)
    except Exception:
        result.warnings.append(
            "No se pudieron leer los metadatos nativos de la imagen; podría estar dañada."
        )
    return limited(result, "Imagen")
