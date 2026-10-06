"""Proceso aislado por análisis: timeout, memoria acotada y respuesta sólo JSON."""

import json
import logging
import math
import multiprocessing
import os
from multiprocessing.connection import Connection
from pathlib import Path

from app.core.config import settings
from app.core.errors import ExtractionError
from app.models.schemas import MessageMetadata


def _timeout_for_size(size: int) -> int:
    """Escala el plazo de un archivo grande sin imponer un máximo de carga."""
    throughput = max(1, settings.minimum_processing_bytes_per_second)
    return max(settings.extraction_timeout_seconds, math.ceil(size / throughput))


def _worker(connection: Connection, path: str, filename: str, size: int) -> None:
    try:
        logging.disable(logging.CRITICAL)  # Los parsers no deben imprimir datos de correos.
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
        from app.services.message_extractor import extract_msg_file

        result = extract_msg_file(Path(path), filename, size)
        connection.send_bytes(result.model_dump_json().encode())
    except ExtractionError as error:
        connection.send_bytes(json.dumps({"error": str(error), "code": error.code}).encode())
    except Exception:
        connection.send_bytes(
            b'{"error":"No fue posible completar la lectura del archivo.",'
            b'"code":"EXTRACTION_FAILED"}'
        )
    finally:
        connection.close()


def _attachment_worker(
    connection: Connection, path: str, attachment_index: int, destination: str
) -> None:
    try:
        logging.disable(logging.CRITICAL)
        from app.services.message_extractor import extract_attachment_file

        filename, content_type = extract_attachment_file(
            Path(path), attachment_index, Path(destination)
        )
        connection.send_bytes(
            json.dumps({"filename": filename, "content_type": content_type}).encode()
        )
    except ExtractionError as error:
        connection.send_bytes(json.dumps({"error": str(error), "code": error.code}).encode())
    except Exception:
        connection.send_bytes(
            b'{"error":"No fue posible preparar el adjunto para descargar.",'
            b'"code":"ATTACHMENT_FAILED"}'
        )
    finally:
        connection.close()


def run_extraction(path: Path, filename: str, size: int) -> MessageMetadata:
    context = multiprocessing.get_context("spawn")
    receiver, sender = context.Pipe(duplex=False)
    process = context.Process(target=_worker, args=(sender, str(path), filename, size))
    timeout = _timeout_for_size(size)
    try:
        process.start()
        sender.close()
        if not receiver.poll(timeout):
            raise ExtractionError(
                f"El análisis excedió {timeout} segundos. Compruebe que el archivo esté completo "
                "e inténtelo de nuevo.",
                code="EXTRACTION_TIMEOUT",
            )
        try:
            payload = json.loads(receiver.recv_bytes(maxlength=20 * 1024 * 1024))
        except (EOFError, OSError, ValueError) as error:
            raise ExtractionError(
                "El lector agotó sus recursos o encontró un archivo ilegible.", code="WORKER_FAILED"
            ) from error
        if "error" in payload:
            raise ExtractionError(payload["error"], code=payload["code"])
        return MessageMetadata.model_validate(payload)
    finally:
        sender.close()
        receiver.close()
        if process.pid:
            process.join(timeout=1)
            if process.is_alive():
                process.terminate()
                process.join(timeout=2)
            if process.is_alive():
                process.kill()
                process.join(timeout=2)
            process.close()


def run_attachment_extraction(
    path: Path, size: int, attachment_index: int, destination: Path
) -> tuple[str, str]:
    """Aísla también la extracción de un binario antes de entregarlo al navegador."""
    context = multiprocessing.get_context("spawn")
    receiver, sender = context.Pipe(duplex=False)
    process = context.Process(
        target=_attachment_worker,
        args=(sender, str(path), attachment_index, str(destination)),
    )
    timeout = _timeout_for_size(size)
    try:
        process.start()
        sender.close()
        if not receiver.poll(timeout):
            raise ExtractionError(
                f"La preparación del adjunto excedió {timeout} segundos.",
                code="EXTRACTION_TIMEOUT",
            )
        try:
            payload = json.loads(receiver.recv_bytes(maxlength=64 * 1024))
        except (EOFError, OSError, ValueError) as error:
            raise ExtractionError(
                "No fue posible preparar el adjunto para descargar.", code="ATTACHMENT_FAILED"
            ) from error
        if "error" in payload:
            raise ExtractionError(payload["error"], code=payload["code"])
        return str(payload["filename"]), str(payload["content_type"])
    finally:
        sender.close()
        receiver.close()
        if process.pid:
            process.join(timeout=1)
            if process.is_alive():
                process.terminate()
                process.join(timeout=2)
            if process.is_alive():
                process.kill()
                process.join(timeout=2)
            process.close()
