"""Metadatos genéricos con ExifTool, si está instalado, en modo sólo lectura y con límites.

El adjunto se envía por stdin (nunca una ruta ni un nombre), los argumentos son constantes, la
salida se corta en ``EXIFTOOL_STDOUT_MAX_BYTES`` y el proceso se termina al agotar el plazo.
"""

import json
import shutil
import subprocess
import threading
import time
from collections.abc import Mapping

from app.services.metadata.results import ExtractionResult, add_item, limited

EXIFTOOL_TIMEOUT_SECONDS = 15
EXIFTOOL_STDOUT_MAX_BYTES = 1024 * 1024
_EXCLUDED_TAGS = {"SourceFile", "File:FileName", "File:Directory", "File:FileModifyDate"}
_TIMEOUT_NOTICE = "ExifTool agotó el tiempo de lectura; se conservaron los metadatos nativos."


def exiftool_metadata(
    payload: bytes, _filename: str, *, deadline: float | None = None
) -> ExtractionResult:
    """Consulta ExifTool en sólo lectura; nombres y rutas nunca llegan al proceso.

    No se usa ``-FileName=`` porque es una asignación de etiqueta (escritura).
    La única entrada es ``-`` por stdin y los argumentos son constantes.
    """
    result = ExtractionResult()
    executable = shutil.which("exiftool")
    if not executable:
        result.warnings.append(
            "ExifTool no está disponible; se muestran sólo metadatos nativos cuando existen."
        )
        return result
    timeout = _external_timeout(deadline)
    if timeout <= 0:
        result.warnings.append(
            "ExifTool se omitió porque agotó el presupuesto de tiempo del adjunto."
        )
        return result
    stdout = _run_exiftool(executable, payload, timeout, result.warnings)
    if stdout is not None:
        _parse_output(stdout, result)
    return limited(result, "ExifTool")


def _run_exiftool(
    executable: str, payload: bytes, timeout: float, warnings: list[str]
) -> bytes | None:
    """Ejecuta ExifTool con hilos de lectura y escritura; ``None`` si hubo que abortarlo."""
    process = None
    stdout = bytearray()
    output_too_large = threading.Event()
    finish_at = time.monotonic() + timeout
    try:
        process = subprocess.Popen(
            [executable, "-j", "-G1", "-s", "-"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            shell=False,
        )
        if process.stdout is None:
            raise OSError("ExifTool no expuso stdout")
        reader = threading.Thread(
            target=_read_limited_stdout,
            args=(process.stdout, stdout, output_too_large),
            daemon=True,
        )
        reader.start()
        if process.stdin is not None:
            threading.Thread(
                target=_write_stdin, args=(process.stdin, payload), daemon=True
            ).start()
        reader.join(timeout=max(0, finish_at - time.monotonic()))
        if output_too_large.is_set():
            _stop_process(process)
            warnings.append("ExifTool devolvió más de 1 MiB de metadata; se omitió su salida.")
            return None
        if reader.is_alive():
            _stop_process(process)
            warnings.append(_TIMEOUT_NOTICE)
            return None
        try:
            process.wait(timeout=max(0, finish_at - time.monotonic()))
        except subprocess.TimeoutExpired:
            _stop_process(process)
            warnings.append(_TIMEOUT_NOTICE)
            return None
        if process.returncode:
            warnings.append("ExifTool informó una advertencia o error al leer el archivo.")
    except OSError:
        if process is not None:
            _stop_process(process)
        warnings.append("No se pudo iniciar ExifTool; se conservaron los metadatos nativos.")
        return None
    finally:
        if process is not None and process.poll() is not None:
            _close_streams(process)
    return bytes(stdout)


def _parse_output(stdout: bytes, result: ExtractionResult) -> None:
    try:
        decoded = json.loads(stdout.decode("utf-8", errors="replace"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        result.warnings.append("ExifTool no devolvió JSON de metadatos válido.")
        return
    if not isinstance(decoded, list) or not decoded or not isinstance(decoded[0], Mapping):
        result.warnings.append("ExifTool no devolvió metadatos para este formato.")
        return
    for key, value in decoded[0].items():
        if key not in _EXCLUDED_TAGS:
            add_item(result, "ExifTool", str(key), value)
    if not result.items:
        result.warnings.append("ExifTool no devolvió metadatos aprovechables para este formato.")


def _read_limited_stdout(stream: object, buffer: bytearray, too_large: threading.Event) -> None:
    """Lee stdout hasta el presupuesto; no deja a ExifTool llenar memoria."""
    try:
        while True:
            chunk = stream.read(64 * 1024)
            if not chunk:
                return
            remaining = EXIFTOOL_STDOUT_MAX_BYTES - len(buffer)
            if len(chunk) > remaining:
                buffer.extend(chunk[: max(remaining, 0)])
                too_large.set()
                return
            buffer.extend(chunk)
    except (OSError, ValueError):
        # El proceso puede cerrar stdout al ser terminado por timeout.
        return
    finally:
        try:
            stream.close()
        except (OSError, ValueError):
            pass


def _write_stdin(stream: object, payload: bytes) -> None:
    """No bloquea al hilo de extracción si una herramienta deja de leer stdin."""
    try:
        stream.write(payload)
    except (BrokenPipeError, OSError, ValueError):
        pass
    finally:
        try:
            stream.close()
        except (OSError, ValueError):
            pass


def _close_streams(process: subprocess.Popen[bytes]) -> None:
    for stream in (process.stdin, process.stdout):
        if stream is not None:
            try:
                stream.close()
            except (OSError, ValueError):
                pass


def _stop_process(process: subprocess.Popen[bytes]) -> None:
    """Termina y espera al proceso externo antes de soltar sus pipes."""
    try:
        if process.poll() is None:
            process.kill()
        process.wait(timeout=2)
    except (OSError, subprocess.TimeoutExpired):
        try:
            if process.poll() is None:
                process.terminate()
            process.wait(timeout=2)
        except (OSError, subprocess.TimeoutExpired):
            # Es un último recurso excepcional: los pipes se cierran para no
            # retener handles de la aplicación aunque el SO tarde en recogerlo.
            pass
    finally:
        _close_streams(process)


def _external_timeout(deadline: float | None) -> float:
    """Combina el límite por herramienta y el presupuesto global del adjunto."""
    if deadline is None:
        return float(EXIFTOOL_TIMEOUT_SECONDS)
    return min(float(EXIFTOOL_TIMEOUT_SECONDS), deadline - time.monotonic())
