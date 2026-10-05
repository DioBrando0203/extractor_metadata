"""Proceso aislado por análisis: timeout, memoria acotada y respuesta sólo JSON."""

import json
import logging
import multiprocessing
import os
from multiprocessing.connection import Connection
from pathlib import Path

from app.core.config import settings
from app.core.errors import ExtractionError
from app.models.schemas import MessageMetadata


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


def run_extraction(path: Path, filename: str, size: int) -> MessageMetadata:
    context = multiprocessing.get_context("spawn")
    receiver, sender = context.Pipe(duplex=False)
    process = context.Process(target=_worker, args=(sender, str(path), filename, size))
    try:
        process.start()
        sender.close()
        if not receiver.poll(settings.extraction_timeout_seconds):
            raise ExtractionError(
                f"El análisis excedió {settings.extraction_timeout_seconds} segundos. "
                "Intente un archivo más pequeño "
                "o compruebe que esté completo.",
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
