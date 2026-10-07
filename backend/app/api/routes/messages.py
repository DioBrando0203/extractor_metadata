import re
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory, mkdtemp
from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask
from starlette.concurrency import run_in_threadpool

from app.core.config import settings
from app.core.errors import ExtractionError
from app.models.schemas import ExtractionResponse
from app.services.worker import AttachmentRequest, run_attachment_extraction, run_extraction

router = APIRouter()
#: Índices de correos adjuntos separados por "/" (``"2/0"``); vacío = el correo principal.
_MESSAGE_PATH = r"^(\d{1,4}(/\d{1,4})*)?$"


async def _copy_upload(file: UploadFile, target: Path) -> int:
    total = 0
    with target.open("wb") as output:
        while chunk := await file.read(1024 * 1024):
            total += len(chunk)
            output.write(chunk)
    return total


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
            total = await _copy_upload(file, target)
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


@router.post("/attachment")
async def download_attachment(
    request: Request,
    file: Annotated[UploadFile, File()],
    attachment_index: Annotated[int, Form(ge=0)],
    preview: Annotated[bool, Form()] = False,
    message_path: Annotated[str, Form(max_length=64, pattern=_MESSAGE_PATH)] = "",
) -> FileResponse:
    filename = re.split(r"[/\\]", file.filename or "mensaje.msg")[-1]
    directory: Path | None = None
    try:
        if Path(filename).suffix.lower() != ".msg":
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="Seleccione un archivo .msg.",
            )
        request_data = _attachment_request(attachment_index, message_path, preview)
        settings.temp_root.mkdir(parents=True, exist_ok=True)
        directory = Path(mkdtemp(prefix="download-", dir=settings.temp_root))
        target = directory / "input.msg"
        output = directory / "attachment.bin"
        total = await _copy_upload(file, target)
        async with request.app.state.extraction_slots:
            download_name, content_type = await run_in_threadpool(
                run_attachment_extraction, target, total, request_data, output
            )
        return FileResponse(
            output,
            media_type=content_type,
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


def _attachment_request(index: int, message_path: str, preview: bool) -> AttachmentRequest:
    path = tuple(int(part) for part in message_path.split("/") if part)
    if len(path) > settings.max_embedded_depth:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={"code": "ATTACHMENT_NOT_FOUND", "message": "Ruta de correo adjunto inválida."},
        )
    return AttachmentRequest(index=index, message_path=path, preview=preview)
