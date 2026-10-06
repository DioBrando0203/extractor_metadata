"""Proceso aislado por solicitud: plazo proporcional al tamaño, memoria acotada y respuesta JSON.

El proceso padre (FastAPI) nunca interpreta el MSG. Cada tarea corre en un hijo ``spawn`` que sólo
devuelve JSON por un pipe; si se cuelga, se termina y se informa un error seguro.
"""

import json
import logging
import math
import multiprocessing
import os
from collections.abc import Callable
from dataclasses import dataclass
from multiprocessing.connection import Connection
from multiprocessing.process import BaseProcess
from pathlib import Path

from app.core.config import settings
from app.core.errors import ExtractionError
from app.models.schemas import MessageMetadata

_ANALYSIS_RESPONSE_BYTES = 20 * 1024 * 1024
_ATTACHMENT_RESPONSE_BYTES = 64 * 1024
_ANALYSIS_FALLBACK = (
    b'{"error":"No fue posible completar la lectura del archivo.","code":"EXTRACTION_FAILED"}'
)
_ATTACHMENT_FALLBACK = (
    b'{"error":"No fue posible preparar el adjunto para descargar.","code":"ATTACHMENT_FAILED"}'
)


@dataclass(frozen=True)
class _IsolatedJob:
    """Qué ejecutar en el hijo y cómo informar sus fallos."""

    target: Callable[..., None]
    args: tuple[object, ...]
    timeout: int
    max_response_bytes: int
    timeout_message: str
    failure_message: str
    failure_code: str


def _timeout_for_size(size: int) -> int:
    """Escala el plazo de un archivo grande sin imponer un máximo de carga."""
    throughput = max(1, settings.minimum_processing_bytes_per_second)
    return max(settings.extraction_timeout_seconds, math.ceil(size / throughput))


# Lado hijo ----------------------------------------------------------------------------------------


def _harden_child() -> None:
    """Sin logs con datos de correos, un hilo de cálculo y memoria virtual acotada si se puede."""
    logging.disable(logging.CRITICAL)
    os.environ["OPENBLAS_NUM_THREADS"] = "1"
    os.environ["OMP_NUM_THREADS"] = "1"
    try:
        import resource

        resource.setrlimit(
            resource.RLIMIT_AS,
            (settings.max_worker_memory_bytes, settings.max_worker_memory_bytes),
        )
    except (ImportError, OSError, ValueError):
        pass  # Windows no dispone de resource; conserva timeout y límites de bytes.


def _respond(connection: Connection, task: Callable[[], bytes], fallback: bytes) -> None:
    """Ejecuta la tarea y envía sólo JSON: resultado, error seguro o diagnóstico genérico."""
    try:
        _harden_child()
        connection.send_bytes(task())
    except ExtractionError as error:
        connection.send_bytes(json.dumps({"error": str(error), "code": error.code}).encode())
    except Exception:
        connection.send_bytes(fallback)
    finally:
        connection.close()


def _worker(connection: Connection, path: str, filename: str, size: int) -> None:
    def task() -> bytes:
        from app.services.msg import extract_msg_file

        return extract_msg_file(Path(path), filename, size).model_dump_json().encode()

    _respond(connection, task, _ANALYSIS_FALLBACK)


def _attachment_worker(
    connection: Connection, path: str, attachment_index: int, destination: str, preview: bool
) -> None:
    def task() -> bytes:
        from app.services.msg import extract_attachment_file

        target = Path(destination)
        filename, content_type = extract_attachment_file(Path(path), attachment_index, target)
        if preview:
            from app.services.previews import write_large_preview

            filename, content_type = write_large_preview(target, filename)
        return json.dumps({"filename": filename, "content_type": content_type}).encode()

    _respond(connection, task, _ATTACHMENT_FALLBACK)


# Lado padre ---------------------------------------------------------------------------------------


def run_extraction(path: Path, filename: str, size: int) -> MessageMetadata:
    timeout = _timeout_for_size(size)
    payload = _run_isolated(
        _IsolatedJob(
            target=_worker,
            args=(str(path), filename, size),
            timeout=timeout,
            max_response_bytes=_ANALYSIS_RESPONSE_BYTES,
            timeout_message=(
                f"El análisis excedió {timeout} segundos. Compruebe que el archivo esté completo "
                "e inténtelo de nuevo."
            ),
            failure_message="El lector agotó sus recursos o encontró un archivo ilegible.",
            failure_code="WORKER_FAILED",
        )
    )
    return MessageMetadata.model_validate(payload)


def run_attachment_extraction(
    path: Path, size: int, attachment_index: int, destination: Path, preview: bool = False
) -> tuple[str, str]:
    """Aísla también la extracción de un binario antes de entregarlo al navegador.

    Con ``preview`` entrega una imagen JPEG del adjunto en lugar del archivo original.
    """
    timeout = _timeout_for_size(size)
    payload = _run_isolated(
        _IsolatedJob(
            target=_attachment_worker,
            args=(str(path), attachment_index, str(destination), preview),
            timeout=timeout,
            max_response_bytes=_ATTACHMENT_RESPONSE_BYTES,
            timeout_message=f"La preparación del adjunto excedió {timeout} segundos.",
            failure_message="No fue posible preparar el adjunto para descargar.",
            failure_code="ATTACHMENT_FAILED",
        )
    )
    return str(payload["filename"]), str(payload["content_type"])


def _run_isolated(job: _IsolatedJob) -> dict:
    """Lanza el hijo, espera su JSON dentro del plazo y garantiza que no quede vivo."""
    context = multiprocessing.get_context("spawn")
    receiver, sender = context.Pipe(duplex=False)
    process = context.Process(target=job.target, args=(sender, *job.args))
    try:
        process.start()
        sender.close()
        if not receiver.poll(job.timeout):
            raise ExtractionError(job.timeout_message, code="EXTRACTION_TIMEOUT")
        try:
            payload = json.loads(receiver.recv_bytes(maxlength=job.max_response_bytes))
        except (EOFError, OSError, ValueError) as error:
            raise ExtractionError(job.failure_message, code=job.failure_code) from error
        if "error" in payload:
            raise ExtractionError(payload["error"], code=payload["code"])
        return payload
    finally:
        sender.close()
        receiver.close()
        _reap(process)


def _reap(process: BaseProcess) -> None:
    """Espera al hijo; si sigue vivo lo termina y, como último recurso, lo mata."""
    if not process.pid:
        return
    process.join(timeout=1)
    if process.is_alive():
        process.terminate()
        process.join(timeout=2)
    if process.is_alive():
        process.kill()
        process.join(timeout=2)
    process.close()
