"""Extracción defensiva de metadatos de adjuntos, sin persistir su contenido."""

from __future__ import annotations

import json
import mimetypes
import shutil
import subprocess
import threading
import time
import zipfile
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from io import BytesIO, StringIO
from pathlib import Path
from xml.etree import ElementTree

from app.core.config import settings
from app.models.schemas import MetadataItem

MAX_ARCHIVE_MEMBERS = 2_000
MAX_ARCHIVE_UNCOMPRESSED_BYTES = 128 * 1024 * 1024
MAX_ARCHIVE_MEMBER_BYTES = 32 * 1024 * 1024
MAX_ARCHIVE_COMPRESSION_RATIO = 200
MAX_OFFICE_XML_BYTES = 2 * 1024 * 1024
EXIFTOOL_TIMEOUT_SECONDS = 15
EXIFTOOL_STDOUT_MAX_BYTES = 1024 * 1024
_CFB_SIGNATURE = bytes.fromhex("D0CF11E0A1B11AE1")
_PDF_SIGNATURE = b"%PDF-"
_DWG_VERSIONS = {
    "AC1001": "AutoCAD R2.0",
    "AC1002": "AutoCAD R2.5",
    "AC1003": "AutoCAD R2.6",
    "AC1004": "AutoCAD R9",
    "AC1006": "AutoCAD R10",
    "AC1009": "AutoCAD R11/R12",
    "AC1012": "AutoCAD R13",
    "AC1014": "AutoCAD R14",
    "AC1015": "AutoCAD 2000",
    "AC1018": "AutoCAD 2004",
    "AC1021": "AutoCAD 2007",
    "AC1024": "AutoCAD 2010",
    "AC1027": "DWG 2013 (formato)",
    "AC1032": "DWG 2018 (formato)",
}


@dataclass(frozen=True)
class _DetectedFile:
    kind: str
    content_type: str | None
    extension: str
    signature: str


@dataclass
class _ExtractionResult:
    items: list[MetadataItem] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class _NativeExtractor:
    name: str
    matches: Callable[[_DetectedFile], bool]
    extract: Callable[[bytes, _DetectedFile], _ExtractionResult]


class _UnsafeOfficeArchive(ValueError):
    """ZIP Office cuya descompresión no es segura para el proceso local."""


def _stringify(value: object) -> tuple[str, bool]:
    """Da una representación pequeña, serializable y sin binarios en la respuesta."""
    if isinstance(value, bytes):
        text = f"<binario: {len(value):,} bytes>"
    elif isinstance(value, (dict, list, tuple)):
        try:
            text = json.dumps(value, ensure_ascii=False, default=str)
        except (TypeError, ValueError):
            text = str(value)
    else:
        text = str(value)
    if len(text) <= settings.max_property_chars:
        return text, False
    return (
        f"{text[: settings.max_property_chars]} … [truncado; {len(text):,} caracteres en origen]",
        True,
    )


def _add(result: _ExtractionResult, group: str, label: str, value: object) -> None:
    safe_group, group_cut = _stringify(group)
    safe_label, label_cut = _stringify(label)
    safe_value, value_cut = _stringify(value)
    if len(safe_label) > 256:
        safe_label = f"{safe_label[:256]} …"
        label_cut = True
    result.items.append(MetadataItem(group=safe_group, label=safe_label, value=safe_value))
    if group_cut or label_cut or value_cut:
        result.warnings.append(
            "Se truncó un valor de metadatos demasiado grande para la respuesta."
        )


def _limited(result: _ExtractionResult, source: str) -> _ExtractionResult:
    if len(result.items) > settings.max_properties:
        omitted = len(result.items) - settings.max_properties
        result.items = result.items[: settings.max_properties]
        result.warnings.append(
            f"{source}: se omitieron {omitted:,} metadatos para mantener una respuesta legible."
        )
    result.warnings = list(dict.fromkeys(result.warnings))
    return result


def _image_signature(payload: bytes) -> tuple[str, str, str] | None:
    if payload.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image", "image/png", "PNG"
    if payload.startswith(b"\xff\xd8\xff"):
        return "image", "image/jpeg", "JPEG"
    if payload.startswith((b"GIF87a", b"GIF89a")):
        return "image", "image/gif", "GIF"
    if payload.startswith(b"BM"):
        return "image", "image/bmp", "BMP"
    if payload.startswith((b"II*\x00", b"MM\x00*")):
        return "image", "image/tiff", "TIFF"
    if payload.startswith(b"RIFF") and payload[8:12] == b"WEBP":
        return "image", "image/webp", "WebP"
    return None


def _zip_kind(payload: bytes) -> tuple[str, str | None, str] | None:
    """Reconoce OOXML leyendo sólo el directorio ZIP, no hojas ni documento."""
    try:
        with zipfile.ZipFile(BytesIO(payload)) as archive:
            names = set(archive.namelist())
    except (OSError, zipfile.BadZipFile):
        return None
    if "xl/workbook.xml" in names:
        return (
            "xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "ZIP/OOXML Excel",
        )
    if "word/document.xml" in names:
        return (
            "docx",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "ZIP/OOXML Word",
        )
    if "ppt/presentation.xml" in names:
        return (
            "pptx",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            "ZIP/OOXML PowerPoint",
        )
    return "zip", "application/zip", "ZIP"


def _looks_like_dxf(payload: bytes) -> bool:
    head = payload[:2_048].decode("latin-1", errors="ignore").upper()
    return "SECTION" in head and ("HEADER" in head or "ENTITIES" in head)


def _detect_file(payload: bytes, filename: str) -> _DetectedFile:
    extension = Path(filename).suffix.lower()
    image = _image_signature(payload)
    if image:
        kind, content_type, signature = image
        return _DetectedFile(kind, content_type, extension, signature)
    if payload.startswith(_PDF_SIGNATURE):
        return _DetectedFile("pdf", "application/pdf", extension, "PDF")
    if payload.startswith(_CFB_SIGNATURE):
        office_types = {
            ".xls": "application/vnd.ms-excel",
            ".doc": "application/msword",
            ".ppt": "application/vnd.ms-powerpoint",
        }
        return _DetectedFile(
            "ole", office_types.get(extension, "application/x-ole-storage"), extension, "OLE/CFB"
        )
    if payload.startswith((b"PK\x03\x04", b"PK\x05\x06")):
        ooxml = _zip_kind(payload)
        if ooxml:
            kind, content_type, signature = ooxml
            return _DetectedFile(kind, content_type, extension, signature)
    if len(payload) >= 6 and payload[:2] == b"AC" and payload[2:6].isdigit():
        return _DetectedFile("dwg", "application/acad", extension, "DWG")
    if extension == ".dxf" or _looks_like_dxf(payload):
        return _DetectedFile("dxf", "application/dxf", extension, "DXF")
    if extension == ".dwg":
        return _DetectedFile(
            "dwg", "application/acad", extension, "Extensión DWG (firma no verificada)"
        )
    return _DetectedFile("generic", mimetypes.guess_type(filename)[0], extension, "No reconocida")


def _image_metadata(payload: bytes, _: _DetectedFile) -> _ExtractionResult:
    result = _ExtractionResult()
    try:
        from PIL import ExifTags, Image

        with Image.open(BytesIO(payload)) as image:
            _add(result, "Imagen", "Formato", image.format or "Desconocido")
            _add(result, "Imagen", "Dimensiones", f"{image.width} × {image.height}")
            _add(result, "Imagen", "Modo", image.mode)
            # Sólo se lee el directorio EXIF; no se decodifican los píxeles.
            for tag, value in image.getexif().items():
                _add(result, "EXIF", str(ExifTags.TAGS.get(tag, f"Etiqueta {tag}")), value)
    except Exception:
        result.warnings.append(
            "No se pudieron leer los metadatos nativos de la imagen; podría estar dañada."
        )
    return _limited(result, "Imagen")


def _pdf_metadata(payload: bytes, _: _DetectedFile) -> _ExtractionResult:
    result = _ExtractionResult()
    stream = BytesIO(payload)
    reader = None
    try:
        from pypdf import PdfReader

        reader = PdfReader(stream, strict=False)
        _add(result, "PDF", "Cifrado", "Sí" if reader.is_encrypted else "No")
        if reader.is_encrypted:
            result.warnings.append(
                "El PDF está cifrado; no se intentó descifrar ni leer su contenido."
            )
            return result
        _add(result, "PDF", "Páginas", len(reader.pages))
        for key, value in (reader.metadata or {}).items():
            if value is not None and str(value):
                _add(result, "PDF", str(key).lstrip("/"), value)
        try:
            xmp = reader.xmp_metadata
            if xmp is not None:
                for name in (
                    "dc_title",
                    "dc_creator",
                    "dc_description",
                    "dc_subject",
                    "dc_rights",
                    "xmp_create_date",
                    "xmp_modify_date",
                    "pdf_keywords",
                    "pdf_producer",
                ):
                    value = getattr(xmp, name, None)
                    if value:
                        _add(result, "PDF / XMP", name, value)
        except Exception:
            result.warnings.append("XMP del PDF ilegible; se conservan las demás propiedades.")
    except Exception:
        result.warnings.append(
            "No se pudieron leer los metadatos PDF; el archivo podría estar truncado o dañado."
        )
    finally:
        close = getattr(reader, "close", None)
        if callable(close):
            close()
        stream.close()
    return _limited(result, "PDF")


def _validate_office_archive(archive: zipfile.ZipFile) -> None:
    infos = archive.infolist()
    if len(infos) > MAX_ARCHIVE_MEMBERS:
        raise _UnsafeOfficeArchive("demasiados elementos ZIP")
    total = 0
    for info in infos:
        if info.file_size > MAX_ARCHIVE_MEMBER_BYTES:
            raise _UnsafeOfficeArchive("un componente ZIP excede el límite")
        total += info.file_size
        if total > MAX_ARCHIVE_UNCOMPRESSED_BYTES:
            raise _UnsafeOfficeArchive("el total ZIP descomprimido excede el límite")
        if info.file_size and (
            not info.compress_size
            or info.file_size / info.compress_size > MAX_ARCHIVE_COMPRESSION_RATIO
        ):
            raise _UnsafeOfficeArchive("relación de compresión sospechosa")


def _read_office_part(archive: zipfile.ZipFile, name: str) -> bytes | None:
    try:
        info = archive.getinfo(name)
    except KeyError:
        return None
    if info.file_size > MAX_OFFICE_XML_BYTES:
        raise _UnsafeOfficeArchive(f"{name} excede el límite XML")
    return archive.read(info)


def _xml_root(content: bytes | None) -> ElementTree.Element | None:
    if not content:
        return None
    try:
        return ElementTree.fromstring(content)
    except ElementTree.ParseError:
        return None


def _local_name(name: str) -> str:
    return name.rsplit("}", 1)[-1]


def _core_properties(root: ElementTree.Element | None, result: _ExtractionResult) -> None:
    if root is None:
        return
    labels = {
        "creator": "Autor",
        "title": "Título",
        "subject": "Asunto",
        "description": "Descripción",
        "created": "Creado",
        "modified": "Modificado",
        "lastModifiedBy": "Última modificación por",
    }
    for child in root:
        key, value = _local_name(child.tag), (child.text or "").strip()
        if value:
            _add(result, "Office", labels.get(key, key), value)


def _office_metadata(payload: bytes, detected: _DetectedFile) -> _ExtractionResult:
    result = _ExtractionResult()
    try:
        with zipfile.ZipFile(BytesIO(payload)) as archive:
            _validate_office_archive(archive)
            _core_properties(_xml_root(_read_office_part(archive, "docProps/core.xml")), result)
            app_root = _xml_root(_read_office_part(archive, "docProps/app.xml"))
            if app_root is not None:
                for element in app_root:
                    value = (element.text or "").strip()
                    if value:
                        _add(result, "Office / aplicación", _local_name(element.tag), value)
            custom_root = _xml_root(_read_office_part(archive, "docProps/custom.xml"))
            if custom_root is not None:
                for prop in custom_root:
                    value = " ".join(text.strip() for text in prop.itertext() if text.strip())
                    if value:
                        _add(
                            result,
                            "Office / personalizado",
                            prop.attrib.get("name", "Propiedad"),
                            value,
                        )
            if detected.kind == "xlsx":
                root = _xml_root(_read_office_part(archive, "xl/workbook.xml"))
                if root is None:
                    result.warnings.append("No se encontró el libro XML de Excel.")
                else:
                    sheets = [
                        element.attrib["name"]
                        for element in root.iter()
                        if _local_name(element.tag) == "sheet" and element.attrib.get("name")
                    ]
                    _add(result, "Excel", "Cantidad de hojas", len(sheets))
                    if sheets:
                        _add(result, "Excel", "Hojas", ", ".join(sheets))
            elif detected.kind == "docx":
                _add(result, "Office", "Formato", "Word Open XML")
            else:
                _add(result, "Office", "Formato", "PowerPoint Open XML")
    except _UnsafeOfficeArchive as error:
        result.warnings.append(f"No se inspeccionó Office: {error}.")
    except (OSError, zipfile.BadZipFile):
        result.warnings.append(
            "No se pudieron leer los metadatos Office; el contenedor ZIP está dañado."
        )
    return _limited(result, "Office")


def _dxf_metadata(payload: bytes, _: _DetectedFile) -> _ExtractionResult:
    result = _ExtractionResult()
    try:
        import ezdxf

        document = ezdxf.read(StringIO(payload.decode("latin-1")))
        _add(result, "AutoCAD", "Formato", document.dxfversion)
        _add(result, "AutoCAD", "Unidades", document.header.get("$INSUNITS", "No definidas"))
        _add(result, "AutoCAD", "Capas", len(document.layers))
    except Exception:
        result.warnings.append(
            "No se pudieron leer los metadatos DXF; el archivo podría estar dañado "
            "o no ser DXF ASCII compatible."
        )
    return _limited(result, "DXF")


def _dwg_metadata(payload: bytes, _: _DetectedFile) -> _ExtractionResult:
    result = _ExtractionResult()
    code = payload[:6].decode("ascii", errors="replace")
    if code in _DWG_VERSIONS:
        _add(result, "AutoCAD", "Firma DWG", code)
        _add(result, "AutoCAD", "Versión de formato", _DWG_VERSIONS[code])
    else:
        _add(result, "AutoCAD", "Firma DWG", code or "No disponible")
        result.warnings.append("No se reconoció una firma DWG válida en el encabezado.")
    result.warnings.append(
        "La extracción profunda de propiedades DWG no está disponible; "
        "se muestra sólo la firma de formato."
    )
    return result


_NATIVE_EXTRACTORS = (
    _NativeExtractor("imagen", lambda detected: detected.kind == "image", _image_metadata),
    _NativeExtractor("pdf", lambda detected: detected.kind == "pdf", _pdf_metadata),
    _NativeExtractor(
        "office", lambda detected: detected.kind in {"xlsx", "docx", "pptx"}, _office_metadata
    ),
    _NativeExtractor("dxf", lambda detected: detected.kind == "dxf", _dxf_metadata),
    _NativeExtractor("dwg", lambda detected: detected.kind == "dwg", _dwg_metadata),
)


def _native_metadata(payload: bytes, detected: _DetectedFile) -> _ExtractionResult:
    for extractor in _NATIVE_EXTRACTORS:
        if extractor.matches(detected):
            try:
                return extractor.extract(payload, detected)
            except Exception:
                return _ExtractionResult(
                    warnings=[f"El extractor nativo {extractor.name} no pudo procesar el archivo."]
                )
    return _ExtractionResult()


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
        for stream in (process.stdin, process.stdout):
            if stream is not None:
                try:
                    stream.close()
                except (OSError, ValueError):
                    pass


def _external_timeout(deadline: float | None) -> float:
    """Combina el límite por herramienta y el presupuesto global del adjunto."""
    if deadline is None:
        return float(EXIFTOOL_TIMEOUT_SECONDS)
    return min(float(EXIFTOOL_TIMEOUT_SECONDS), deadline - time.monotonic())


def _exiftool_metadata(
    payload: bytes, _filename: str, *, deadline: float | None = None
) -> _ExtractionResult:
    """Consulta ExifTool en sólo lectura; nombres y rutas nunca llegan al proceso.

    No se usa ``-FileName=`` porque es una asignación de etiqueta (escritura).
    La única entrada es ``-`` por stdin y los argumentos son constantes.
    """
    result = _ExtractionResult()
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
                target=_write_stdin,
                args=(process.stdin, payload),
                daemon=True,
            ).start()
        reader.join(timeout=max(0, finish_at - time.monotonic()))
        if output_too_large.is_set():
            _stop_process(process)
            result.warnings.append(
                "ExifTool devolvió más de 1 MiB de metadata; se omitió su salida."
            )
            return result
        if reader.is_alive():
            _stop_process(process)
            result.warnings.append(
                "ExifTool agotó el tiempo de lectura; se conservaron los metadatos nativos."
            )
            return result
        try:
            process.wait(timeout=max(0, finish_at - time.monotonic()))
        except subprocess.TimeoutExpired:
            _stop_process(process)
            result.warnings.append(
                "ExifTool agotó el tiempo de lectura; se conservaron los metadatos nativos."
            )
            return result
        if process.returncode:
            result.warnings.append("ExifTool informó una advertencia o error al leer el archivo.")
    except OSError:
        if process is not None:
            _stop_process(process)
        result.warnings.append("No se pudo iniciar ExifTool; se conservaron los metadatos nativos.")
        return result
    finally:
        if process is not None and process.poll() is not None:
            for stream in (process.stdin, process.stdout):
                if stream is not None:
                    try:
                        stream.close()
                    except (OSError, ValueError):
                        pass
    try:
        decoded = json.loads(bytes(stdout).decode("utf-8", errors="replace"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        result.warnings.append("ExifTool no devolvió JSON de metadatos válido.")
        return result
    if not isinstance(decoded, list) or not decoded or not isinstance(decoded[0], Mapping):
        result.warnings.append("ExifTool no devolvió metadatos para este formato.")
        return result
    excluded = {"SourceFile", "File:FileName", "File:Directory", "File:FileModifyDate"}
    for key, value in decoded[0].items():
        if key not in excluded:
            _add(result, "ExifTool", str(key), value)
    if not result.items:
        result.warnings.append("ExifTool no devolvió metadatos aprovechables para este formato.")
    return _limited(result, "ExifTool")


def extract_file_metadata(
    payload: bytes, filename: str, *, external_deadline: float | None = None
) -> tuple[str | None, list[MetadataItem], list[str]]:
    """Devuelve resultado parcial para todo adjunto, incluso con formato inválido."""
    detected = _detect_file(payload, filename)
    base = _ExtractionResult()
    _add(base, "Archivo", "Nombre", filename)
    _add(base, "Archivo", "Extensión", detected.extension or "Sin extensión")
    _add(base, "Archivo", "Tamaño", f"{len(payload):,} bytes")
    _add(base, "Archivo", "Firma detectada", detected.signature)
    native = _native_metadata(payload, detected)
    external = _exiftool_metadata(payload, filename, deadline=external_deadline)
    combined = _ExtractionResult(
        base.items + native.items + external.items,
        base.warnings + native.warnings + external.warnings,
    )
    if not native.items and not external.items:
        combined.warnings.append(
            "No hay extractor específico para este formato; "
            "se muestran sólo datos genéricos del archivo."
        )
    combined = _limited(combined, "Adjunto")
    return detected.content_type, combined.items, combined.warnings
