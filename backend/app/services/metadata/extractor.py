"""Punto de entrada de metadatos de adjuntos.

Patrón Strategy: cada formato tiene un extractor con la firma ``(payload, detected) -> result``
registrado en ``NATIVE_EXTRACTORS``. Añadir un formato es crear su módulo y registrarlo aquí; no
se modifica la lógica común.
"""

from collections.abc import Callable
from dataclasses import dataclass

from app.models.schemas import MetadataItem
from app.services.metadata.cad import dwg_metadata, dxf_metadata
from app.services.metadata.detection import detect_file
from app.services.metadata.exiftool import exiftool_metadata
from app.services.metadata.image import image_metadata
from app.services.metadata.office import office_metadata
from app.services.metadata.pdf import pdf_metadata
from app.services.metadata.results import DetectedFile, ExtractionResult, add_item, limited


@dataclass(frozen=True)
class NativeExtractor:
    name: str
    matches: Callable[[DetectedFile], bool]
    extract: Callable[[bytes, DetectedFile], ExtractionResult]


NATIVE_EXTRACTORS = (
    NativeExtractor("imagen", lambda detected: detected.kind == "image", image_metadata),
    NativeExtractor("pdf", lambda detected: detected.kind == "pdf", pdf_metadata),
    NativeExtractor(
        "office", lambda detected: detected.kind in {"xlsx", "docx", "pptx"}, office_metadata
    ),
    NativeExtractor("dxf", lambda detected: detected.kind == "dxf", dxf_metadata),
    NativeExtractor("dwg", lambda detected: detected.kind == "dwg", dwg_metadata),
)


def native_metadata(payload: bytes, detected: DetectedFile) -> ExtractionResult:
    """Aplica el primer extractor compatible; un fallo interno nunca rompe el análisis."""
    for extractor in NATIVE_EXTRACTORS:
        if extractor.matches(detected):
            try:
                return extractor.extract(payload, detected)
            except Exception:
                return ExtractionResult(
                    warnings=[f"El extractor nativo {extractor.name} no pudo procesar el archivo."]
                )
    return ExtractionResult()


def extract_file_metadata(
    payload: bytes, filename: str, *, external_deadline: float | None = None
) -> tuple[str | None, list[MetadataItem], list[str]]:
    """Devuelve resultado parcial para todo adjunto, incluso con formato inválido."""
    detected = detect_file(payload, filename)
    base = ExtractionResult()
    add_item(base, "Archivo", "Nombre", filename)
    add_item(base, "Archivo", "Extensión", detected.extension or "Sin extensión")
    add_item(base, "Archivo", "Tamaño", f"{len(payload):,} bytes")
    add_item(base, "Archivo", "Firma detectada", detected.signature)
    native = native_metadata(payload, detected)
    external = exiftool_metadata(payload, filename, deadline=external_deadline)
    combined = ExtractionResult(
        base.items + native.items + external.items,
        base.warnings + native.warnings + external.warnings,
    )
    if not native.items and not external.items:
        combined.warnings.append(
            "No hay extractor específico para este formato; "
            "se muestran sólo datos genéricos del archivo."
        )
    combined = limited(combined, "Adjunto")
    return detected.content_type, combined.items, combined.warnings
