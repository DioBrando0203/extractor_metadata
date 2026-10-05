from dataclasses import dataclass
from pathlib import Path
from tempfile import gettempdir


@dataclass(frozen=True)
class Settings:
    app_name: str = "Extractor local de MSG"
    max_upload_bytes: int = 100 * 1024 * 1024
    max_attachments: int = 200
    max_attachment_bytes: int = 50 * 1024 * 1024
    max_total_attachment_bytes: int = 150 * 1024 * 1024
    max_body_chars: int = 100_000
    max_property_chars: int = 8_000
    max_properties: int = 1_000
    max_total_metadata_chars: int = 3_000_000
    extraction_timeout_seconds: int = 90
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
