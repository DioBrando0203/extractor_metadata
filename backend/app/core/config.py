from dataclasses import dataclass
from pathlib import Path
from tempfile import gettempdir


@dataclass(frozen=True)
class Settings:
    app_name: str = "Extractor local de MSG"
    max_body_chars: int = 100_000
    max_property_chars: int = 8_000
    max_properties: int = 1_000
    max_total_metadata_chars: int = 3_000_000
    max_total_preview_chars: int = 8_000_000
    extraction_timeout_seconds: int = 90
    minimum_processing_bytes_per_second: int = 4 * 1024 * 1024
    max_worker_memory_bytes: int = 1024 * 1024 * 1024
    max_concurrent_extractions: int = 2
    temp_root: Path = Path(gettempdir()) / "msg-metadata-extractor"
    allowed_origins: tuple[str, ...] = (
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    )


settings = Settings()
