"""Convierte un KML o KMZ en un GeoPackage mediante GDAL, sin estado persistente."""

import os
import shutil
import subprocess
from pathlib import Path
from zipfile import ZIP_DEFLATED, BadZipFile, ZipFile

from app.core.config import settings
from app.core.errors import ExtractionError

_COPY_CHUNK_BYTES = 1024 * 1024
_KML_SUFFIXES = (".kml", ".kmz")


def convert_to_archive(source: Path, destination: Path, original_name: str, timeout: int) -> str:
    """Convierte ``source`` y empaqueta el GeoPackage en ``destination``."""
    work_dir = destination.parent / "work"
    work_dir.mkdir()
    try:
        kml_path = _extract_kml(source, work_dir)
        gpkg_name = f"{Path(original_name).stem or 'mapa'}.gpkg"
        gpkg_path = work_dir / gpkg_name
        _run_ogr2ogr(kml_path, gpkg_path, timeout)
        with ZipFile(destination, "w", ZIP_DEFLATED) as archive:
            archive.write(gpkg_path, gpkg_name)
        return f"{Path(original_name).stem or 'mapa'} - convertido.zip"
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)


def _extract_kml(source: Path, work_dir: Path) -> Path:
    suffix = source.suffix.lower()
    if suffix == ".kml":
        target = work_dir / "input.kml"
        _copy_limited(source, target)
        return target
    if suffix != ".kmz":
        raise ExtractionError("Seleccione un archivo .kml o .kmz.", code="UNSUPPORTED_GEODATA")
    return _extract_kmz_member(source, work_dir)


def _extract_kmz_member(source: Path, work_dir: Path) -> Path:
    try:
        with ZipFile(source) as archive:
            member = _kml_member(archive)
            info = archive.getinfo(member)
            _validate_member(info.file_size, info.compress_size)
            target = work_dir / "input.kml"
            with archive.open(info) as input_stream, target.open("wb") as output_stream:
                _copy_stream_limited(input_stream, output_stream)
            return target
    except BadZipFile as error:
        raise ExtractionError("El archivo KMZ no es un ZIP válido.", code="INVALID_KMZ") from error


def _kml_member(archive: ZipFile) -> str:
    names = [
        name
        for name in archive.namelist()
        if not name.endswith("/") and name.lower().endswith(".kml")
    ]
    if not names:
        raise ExtractionError("El archivo KMZ no contiene un KML.", code="INVALID_KMZ")
    return next((name for name in names if Path(name).name.lower() == "doc.kml"), names[0])


def _validate_member(size: int, compressed_size: int) -> None:
    if size > settings.max_geodata_bytes:
        raise ExtractionError(
            "El KML dentro del KMZ supera el límite permitido.", code="GEODATA_TOO_LARGE"
        )
    ratio = size / max(compressed_size, 1)
    if ratio > settings.max_kmz_compression_ratio:
        raise ExtractionError("El KMZ tiene una compresión no segura.", code="INVALID_KMZ")


def _copy_limited(source: Path, target: Path) -> None:
    with source.open("rb") as input_stream, target.open("wb") as output_stream:
        _copy_stream_limited(input_stream, output_stream)


def _copy_stream_limited(input_stream: object, output_stream: object) -> None:
    total = 0
    while chunk := input_stream.read(_COPY_CHUNK_BYTES):
        total += len(chunk)
        if total > settings.max_geodata_bytes:
            raise ExtractionError(
                "El archivo supera el límite permitido.", code="GEODATA_TOO_LARGE"
            )
        output_stream.write(chunk)


def _run_ogr2ogr(kml_path: Path, gpkg_path: Path, timeout: int) -> None:
    executable = _ogr2ogr_path()
    if executable is None:
        raise ExtractionError(
            "GDAL no está instalado. Instale GDAL u ogr2ogr para convertir KML/KMZ.",
            code="GDAL_UNAVAILABLE",
        )
    try:
        result = subprocess.run(
            [
                str(executable),
                "-f",
                "GPKG",
                "-nlt",
                "PROMOTE_TO_MULTI",
                str(gpkg_path),
                str(kml_path),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as error:
        raise ExtractionError(
            "La conversión excedió el plazo permitido.", code="GEODATA_TIMEOUT"
        ) from error
    if result.returncode:
        raise ExtractionError(
            "GDAL no pudo convertir el archivo geográfico.", code="GEODATA_FAILED"
        )


def _ogr2ogr_path() -> Path | None:
    configured = os.getenv("APP_GDAL_BIN", "").strip()
    candidates = [Path(configured) / _gdal_name()] if configured else []
    found = shutil.which("ogr2ogr") or shutil.which("ogr2ogr.exe")
    if found:
        candidates.append(Path(found))
    if os.name == "nt":
        user_profile = os.getenv("USERPROFILE", "")
        if user_profile:
            candidates.append(Path(user_profile) / "AppData/Local/Programs/OSGeo4W/bin/ogr2ogr.exe")
        candidates.append(Path("C:/OSGeo4W/bin/ogr2ogr.exe"))
    return next((path for path in candidates if path.is_file()), None)


def _gdal_name() -> str:
    return "ogr2ogr.exe" if os.name == "nt" else "ogr2ogr"
