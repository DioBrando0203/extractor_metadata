import re
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, Request, UploadFile, status
from starlette.concurrency import run_in_threadpool

from app.core.config import settings
from app.core.errors import ExtractionError
from app.models.schemas import ExtractionResponse
from app.services.worker import run_extraction

router = APIRouter()


@router.post("/extract", response_model=ExtractionResponse)
async def extract_message(
    request: Request, file: Annotated[UploadFile, File()]
) -> ExtractionResponse:
    # Ambos separadores: no interpretar una ruta Windows como nombre en Linux.
    filename = re.split(r"[/\\]", file.filename or "mensaje.msg")[-1]
    try:
        if Path(filename).suffix.lower() != ".msg":
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="Seleccione un archivo .msg.",
            )
        settings.temp_root.mkdir(parents=True, exist_ok=True)
        with TemporaryDirectory(prefix="analysis-", dir=settings.temp_root) as directory:
            target = Path(directory) / "input.msg"
            total = 0
            with target.open("wb") as output:
                while chunk := await file.read(1024 * 1024):
                    total += len(chunk)
                    if total > settings.max_upload_bytes:
                        raise HTTPException(
                            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                            detail="El MSG supera el límite local de 100 MB.",
                        )
                    output.write(chunk)
            async with request.app.state.extraction_slots:
                result = await run_in_threadpool(run_extraction, target, filename, total)
            return ExtractionResponse(message=result)
    except ExtractionError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={"code": error.code, "message": str(error)},
        ) from error
    finally:
        await file.close()
