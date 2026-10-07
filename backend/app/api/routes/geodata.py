"""Ruta HTTP efímera para convertir KML/KMZ a GeoPackage."""

import re
import shutil
from pathlib import Path
from tempfile import mkdtemp
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, Request, UploadFile, status
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask
from starlette.concurrency import run_in_threadpool

from app.core.config import settings
from app.core.errors import ExtractionError
from app.services.worker import run_geodata_conversion

router = APIRouter()
_CHUNK_BYTES = 1024 * 1024


@router.post("/convert")
async def convert_geodata(request: Request, file: Annotated[UploadFile, File()]) -> FileResponse:
    """Convierte un KML/KMZ y entrega el GeoPackage dentro de un ZIP temporal."""
    directory: Path | None = None
    try:
        filename = _filename(file)
        suffix = Path(filename).suffix.lower()
        if suffix not in (".kml", ".kmz"):
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="Seleccione un .kml o .kmz.",
            )
        settings.temp_root.mkdir(parents=True, exist_ok=True)
        directory = Path(mkdtemp(prefix="geodata-", dir=settings.temp_root))
        source = directory / f"input{suffix}"
        output = directory / "conversion.zip"
        size = await _copy_upload(file, source)
        async with request.app.state.extraction_slots:
            download_name = await run_in_threadpool(
                run_geodata_conversion, source, size, output, filename
            )
        return FileResponse(
            output,
            media_type="application/zip",
            filename=download_name,
            background=BackgroundTask(shutil.rmtree, directory, ignore_errors=True),
        )
    except ExtractionError as error:
        if directory is not None:
            shutil.rmtree(directory, ignore_errors=True)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={"code": error.code, "message": str(error)},
        ) from error
    except Exception:
        if directory is not None:
            shutil.rmtree(directory, ignore_errors=True)
        raise
    finally:
        await file.close()


async def _copy_upload(file: UploadFile, target: Path) -> int:
    total = 0
    with target.open("wb") as output:
        while chunk := await file.read(_CHUNK_BYTES):
            total += len(chunk)
            if total > settings.max_geodata_bytes:
                raise ExtractionError(
                    "El archivo supera el límite permitido.", code="GEODATA_TOO_LARGE"
                )
            output.write(chunk)
    return total


def _filename(file: UploadFile) -> str:
    return re.split(r"[/\\]", file.filename or "mapa.kmz")[-1]
