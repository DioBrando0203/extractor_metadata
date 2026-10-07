"""Metadatos de adjuntos por formato. API pública: ``extract_file_metadata`` y ``zip_kind``."""

from app.services.metadata.detection import zip_kind
from app.services.metadata.extractor import extract_file_metadata

__all__ = ["extract_file_metadata", "zip_kind"]
