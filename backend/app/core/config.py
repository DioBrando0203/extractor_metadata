import os
from dataclasses import dataclass
from pathlib import Path
from tempfile import gettempdir


def env_list(name: str, default: tuple[str, ...]) -> tuple[str, ...]:
    """Lista separada por comas de una variable de entorno; vacía o ausente conserva ``default``.

    Sólo amplía Host y Origin para el modo LAN opcional (ADR-B12); sin variables, todo es loopback.
    """
    raw = os.getenv(name, "")
    return tuple(item.strip() for item in raw.split(",") if item.strip()) or default


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
    # KML/KMZ es un contenedor no confiable; limita carga, miembro extraído y ratio anti bomba.
    max_geodata_bytes: int = 512 * 1024 * 1024
    max_kmz_compression_ratio: int = 100
    # Correos adjuntos dentro de correos: un MSG anidado sin fin agotaría tiempo y memoria del hijo.
    max_embedded_depth: int = 3
    max_embedded_messages: int = 20
    temp_root: Path = Path(gettempdir()) / "msg-metadata-extractor"
    allowed_origins: tuple[str, ...] = env_list(
        "APP_ALLOWED_ORIGINS",
        (
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:8000",
            "http://127.0.0.1:8000",
        ),
    )
    allowed_hosts: tuple[str, ...] = env_list(
        "APP_ALLOWED_HOSTS",
        ("localhost", "127.0.0.1", "[::1]"),
    )


settings = Settings()
