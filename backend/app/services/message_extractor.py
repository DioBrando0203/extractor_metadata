"""Lectura MSG tolerante: contenido humano, propiedades MAPI y recuperación OLE."""

import codecs
import re
import struct
import time
from datetime import date, datetime
from email.utils import parsedate_to_datetime
from enum import Enum
from itertools import islice
from pathlib import Path

import extract_msg
import olefile
from extract_msg.enums import ErrorBehavior

from app.core.config import settings
from app.core.errors import ExtractionError
from app.models.schemas import AttachmentMetadata, MessageMetadata, MetadataItem
from app.services.body_text import html_to_text
from app.services.file_metadata import extract_file_metadata

_INVALID_NAME = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_RESERVED_NAME = re.compile(r"^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\.|$)", re.I)
_MAPI_LABELS = {
    "001A": "Clase de mensaje",
    "0037": "Asunto",
    "007D": "Encabezados de transporte",
    "0C1A": "Nombre del remitente",
    "0C1F": "Correo del remitente",
    "0E02": "CCO",
    "0E03": "CC",
    "0E04": "Destinatarios",
    "1000": "Cuerpo de texto",
    "1035": "Message-ID",
    "3001": "Nombre",
    "3003": "Dirección",
    "3704": "Nombre corto del adjunto",
    "3707": "Nombre del adjunto",
    "370E": "MIME del adjunto",
}


def _text(value: object | None, limit: int = settings.max_property_chars) -> str | None:
    if value is None:
        return None
    if isinstance(value, bytes):
        return f"Binario: {len(value):,} bytes (contenido omitido)"
    if isinstance(value, Enum):
        value = value.name
    if isinstance(value, (datetime, date)):
        value = value.isoformat()
    text = str(value).strip()
    if len(text) > limit:
        text = text[:limit] + f" … [truncado; {len(text):,} caracteres]"
    return text or None


def _filename_warnings(filename: str) -> list[str]:
    warnings: list[str] = []
    if (
        _INVALID_NAME.search(filename)
        or _RESERVED_NAME.match(filename)
        or filename.rstrip(". ") != filename
    ):
        warnings.append(
            "El nombre puede ser incompatible con Windows. Este análisis usa una "
            "copia temporal de nombre corto; para Outlook pruebe renombrar el original."
        )
    if len(filename) > 150:
        warnings.append("Nombre muy largo: puede superar límites de ruta al abrirlo en Windows.")
    return warnings


def _read_attribute(message: object, name: str, warnings: list[str]) -> object | None:
    try:
        return getattr(message, name, None)
    except Exception:
        warnings.append(
            f"No se pudo recuperar la propiedad {name}; se conserva el resto del mensaje."
        )
        return None


def _read_ole_metadata(
    path: Path,
) -> tuple[list[MetadataItem], dict[str, str], list[str], dict[str, tuple[str, int]]]:
    """Lee streams acotados, sin devolver binarios; sirve también de recuperación parcial."""
    items: list[MetadataItem] = []
    recovered: dict[str, str] = {}
    attachment_info: dict[str, tuple[str, int]] = {}
    warnings: list[str] = []
    try:
        with olefile.OleFileIO(str(path)) as container:
            streams = container.listdir()
            for parts in streams:
                if (
                    len(parts) == 2
                    and parts[0].startswith("__attach")
                    and parts[-1] == "__substg1.0_37010102"
                ):
                    try:
                        name = f"adjunto-{len(attachment_info) + 1}"
                        name_path = [parts[0], "__substg1.0_3707001F"]
                        if container.exists(name_path):
                            with container.openstream(name_path) as name_stream:
                                name = (
                                    name_stream.read(1024)
                                    .decode("utf-16-le", errors="replace")
                                    .rstrip("\x00")
                                )
                        attachment_info[parts[0]] = (name, container.get_size(parts))
                    except Exception:
                        warnings.append("Un adjunto tiene estructura OLE incompleta.")
            ansi_encoding = "cp1252"
            if container.exists("__properties_version1.0"):
                try:
                    raw_props = container.openstream("__properties_version1.0").read(
                        32 + settings.max_properties * 16
                    )
                    for offset in range(32, len(raw_props) - 15, 16):
                        tag = struct.unpack_from("<I", raw_props, offset)[0]
                        if tag == 0x3FFD0003:
                            codepage = struct.unpack_from("<I", raw_props, offset + 8)[0]
                            try:
                                ansi_encoding = codecs.lookup(f"cp{codepage}").name
                            except LookupError:
                                warnings.append(
                                    "Página de códigos desconocida; recuperación ANSI aproximada."
                                )
                            break
                except Exception:
                    warnings.append(
                        "La página de códigos OLE es ilegible; se recupera texto aproximado."
                    )
            if not any(parts[-1].startswith("__substg1.0_") for parts in streams):
                raise ExtractionError(
                    "El archivo OLE no contiene propiedades de un mensaje MSG.", code="NOT_A_MSG"
                )
            if container.parsing_issues:
                warnings.append(
                    "El contenedor OLE presenta inconsistencias; la lectura es parcial."
                )
            for parts in streams[: settings.max_properties]:
                try:
                    name = parts[-1]
                    size = container.get_size(parts)
                    value = f"Binario o estructura: {size:,} bytes (contenido omitido)"
                    if name.startswith("__substg1.0_") and name[-4:] in {"001F", "001E"}:
                        unicode_stream = name.endswith("001F")
                        encoding = "utf-16-le" if unicode_stream else ansi_encoding
                        limit = (settings.max_property_chars + 1) * (2 if unicode_stream else 1)
                        with container.openstream(parts) as stream:
                            data = stream.read(limit)
                        value = data.decode(encoding, errors="replace").rstrip("\x00")
                        if size > limit:
                            value += f" … [truncado; {size:,} bytes]"
                            notice = "Propiedades extensas: algunos valores se muestran abreviados."
                            if notice not in warnings:
                                warnings.append(notice)
                        if len(parts) == 1:
                            recovered[name[12:16]] = value
                    property_id = name[12:16] if name.startswith("__substg1.0_") else ""
                    label = _MAPI_LABELS.get(property_id, name)
                    if len(parts) > 1:
                        label = "/".join(parts[:-1]) + "/" + label
                    items.append(MetadataItem(group="MAPI / OLE", label=label, value=value))
                except Exception:
                    warnings.append(
                        f"Stream OLE ilegible: {'/'.join(parts)}; se conserva el resto."
                    )
            if len(streams) > settings.max_properties:
                warnings.append(
                    f"Se muestran las primeras {settings.max_properties} propiedades OLE."
                )
    except ExtractionError:
        raise
    except Exception as error:
        raise ExtractionError(
            "El contenedor MSG está corrupto o incompleto y no se puede leer.",
            code="INVALID_OR_CORRUPT_MSG",
        ) from error
    return items, recovered, warnings, attachment_info


def _extract_attachments(
    message: object,
    warnings: list[str],
    attachment_info: dict[str, tuple[str, int]],
    external_deadline: float,
) -> list[AttachmentMetadata]:
    """Inicializa cada adjunto bajo demanda, sin materializar la lista completa.

    ``extract-msg`` crea ``Attachment`` al evaluar ``message.attachments`` y
    cada constructor carga su stream de datos. Recorrer los directorios y usar
    ``initAttachmentFunc`` permite procesar y liberar un payload antes de
    crear el siguiente, además de aplicar el límite de cantidad antes de
    inicializarlos.
    """
    attachments: list[AttachmentMetadata] = []
    list_dir = _read_attribute(message, "listDir", warnings)
    init_attachment = _read_attribute(message, "initAttachmentFunc", warnings)
    if not callable(list_dir) or not callable(init_attachment):
        warnings.append("No se pudo enumerar los adjuntos del mensaje.")
        return attachments
    try:
        storage_paths = list_dir(False, True, False)
    except Exception:
        warnings.append("No se pudo enumerar los adjuntos del mensaje.")
        return attachments

    attachment_dirs: list[str] = []
    for parts in storage_paths:
        if parts and parts[0].startswith("__attach") and parts[0] not in attachment_dirs:
            attachment_dirs.append(parts[0])

    total = 0
    for index, attachment_dir in enumerate(attachment_dirs[: settings.max_attachments], start=1):
        name, known_size = attachment_info.get(attachment_dir, (f"adjunto-{index}", 0))
        if (
            known_size > settings.max_attachment_bytes
            or total + known_size > settings.max_total_attachment_bytes
        ):
            attachments.append(
                AttachmentMetadata(
                    name=name,
                    size_bytes=known_size,
                    warnings=["Se omitió el adjunto antes de cargarlo por el límite de recursos."],
                )
            )
            continue
        attachment = None
        payload = None
        try:
            attachment = init_attachment(message, attachment_dir)
            name = (
                _text(_read_attribute(attachment, "longFilename", warnings))
                or _text(_read_attribute(attachment, "shortFilename", warnings))
                or name
            )
            payload = attachment.data
            if not isinstance(payload, bytes):
                attachments.append(
                    AttachmentMetadata(
                        name=name,
                        warnings=[
                            "Adjunto MSG anidado u objeto embebido: no se expande en esta versión."
                        ],
                    )
                )
                continue
            total += len(payload)
            if (
                len(payload) > settings.max_attachment_bytes
                or total > settings.max_total_attachment_bytes
            ):
                attachments.append(
                    AttachmentMetadata(
                        name=name,
                        size_bytes=len(payload),
                        warnings=[
                            "Se omitió el análisis profundo por el límite de recursos de adjuntos."
                        ],
                    )
                )
                continue
            content_type, metadata, attachment_warnings = extract_file_metadata(
                payload, name, external_deadline=external_deadline
            )
            if len(payload) > 10 * 1024 * 1024:
                attachment_warnings.insert(
                    0,
                    "Adjunto mayor de 10 MB: fue leído; algunas extensiones "
                    "de correo pueden ignorarlo.",
                )
            attachments.append(
                AttachmentMetadata(
                    name=name,
                    content_type=content_type,
                    size_bytes=len(payload),
                    metadata=metadata,
                    warnings=attachment_warnings,
                )
            )
        except Exception:
            attachments.append(
                AttachmentMetadata(
                    name=name,
                    warnings=["Adjunto ilegible o corrupto: se conserva el resto del mensaje."],
                )
            )
        finally:
            # ``Attachment`` conserva ``data`` internamente; no se guarda la
            # instancia fuera de esta iteración para que el siguiente adjunto
            # no se sume a la memoria del anterior.
            del payload
            del attachment
    if len(attachment_dirs) > settings.max_attachments:
        warnings.append(
            f"Se muestran los primeros {settings.max_attachments} adjuntos por límite de recursos."
        )
    return attachments


def _fixed_properties(message: object, warnings: list[str]) -> list[MetadataItem]:
    result: list[MetadataItem] = []
    store = _read_attribute(message, "props", warnings)
    if store is None:
        return result
    try:
        for tag, prop in islice(store.items(), settings.max_properties):
            # Los valores variables ya se muestran desde sus streams OLE.
            if hasattr(prop, "value"):
                value = _text(prop.value)
                if value is not None:
                    result.append(
                        MetadataItem(group="Propiedades MAPI", label=f"0x{tag}", value=value)
                    )
    except Exception:
        warnings.append("Algunas propiedades MAPI fijas no pudieron leerse.")
    return result


def _limit_response(message: MessageMetadata) -> MessageMetadata:
    remaining = settings.max_total_metadata_chars
    for collection in [
        message.properties,
        message.headers,
        *(attachment.metadata for attachment in message.attachments),
    ]:
        keep = []
        for item in collection:
            size = len(item.group) + len(item.label) + len(item.value)
            if size <= remaining:
                keep.append(item)
                remaining -= size
        if len(keep) < len(collection):
            if (
                "Metadata extensa: se omitieron campos por el límite total de respuesta."
                not in message.warnings
            ):
                message.warnings.append(
                    "Metadata extensa: se omitieron campos por el límite total de respuesta."
                )
            message.status = "partial"
            collection[:] = keep
    return message


def extract_msg_file(path: Path, original_name: str, size_bytes: int) -> MessageMetadata:
    if not olefile.isOleFile(str(path)):
        raise ExtractionError(
            "El archivo no tiene una firma MSG/OLE válida. Puede estar corrupto "
            "o haber sido renombrado desde otro formato.",
            code="INVALID_OR_CORRUPT_MSG",
        )
    started = time.monotonic()
    properties, recovered, ole_warnings, attachment_info = _read_ole_metadata(path)
    warnings = _filename_warnings(original_name) + ole_warnings
    try:
        message = extract_msg.openMsg(
            str(path),
            delayAttachments=True,
            errorBehavior=(
                ErrorBehavior.ATTACH_NOT_IMPLEMENTED
                | ErrorBehavior.ATTACH_BROKEN
                | ErrorBehavior.STANDARDS_VIOLATION
            ),
        )
    except Exception:
        if not any(recovered.get(key) for key in ("0037", "1000", "0C1A", "0C1F")):
            raise ExtractionError(
                "El contenedor abre, pero no se pudo recuperar contenido del MSG.",
                code="UNREADABLE_MSG",
            ) from None
        warnings.append(
            "El lector MSG falló. Se recuperaron propiedades de texto desde OLE; "
            "adjuntos y fechas pueden faltar."
        )
        body = recovered.get("1000")
        return _limit_response(
            MessageMetadata(
                file_name=original_name,
                file_size_bytes=size_bytes,
                subject=recovered.get("0037"),
                sender=recovered.get("0C1F") or recovered.get("0C1A"),
                recipients=[recovered["0E04"]] if recovered.get("0E04") else [],
                body_preview=body,
                body_truncated=bool(body and "[truncado;" in body),
                properties=properties,
                warnings=warnings,
                status="partial",
            )
        )

    try:
        subject = _text(_read_attribute(message, "subject", warnings))
        sender = _text(_read_attribute(message, "sender", warnings))
        recipients = []
        for key, label in (("to", "Para"), ("cc", "CC"), ("bcc", "CCO")):
            value = _text(_read_attribute(message, key, warnings))
            if value:
                recipients.append(f"{label}: {value}")
        sent_at = _read_attribute(message, "date", warnings)
        if not isinstance(sent_at, datetime):
            sent_at = None
        body_raw = _read_attribute(message, "body", warnings)
        body = str(body_raw) if body_raw else None
        if not body:
            html = _read_attribute(message, "htmlBody", warnings)
            if isinstance(html, (bytes, str)) and html:
                body = html_to_text(html)
        if not body and recovered.get("1000"):
            body = recovered["1000"]
        received_at = None
        try:
            received_at = message.props.getValue("0E060040")
            if not isinstance(received_at, datetime):
                received_at = None
        except Exception:
            warnings.append("No se pudo recuperar la fecha de recepción.")
        truncated = bool(body and len(body) > settings.max_body_chars)
        if truncated:
            warnings.append(f"Cuerpo largo: se muestran {settings.max_body_chars:,} caracteres.")
        headers: list[MetadataItem] = []
        header = _read_attribute(message, "header", warnings)
        if header is not None:
            try:
                headers = [
                    MetadataItem(group="Encabezado", label=key, value=_text(value) or "")
                    for key, value in list(header.items())[: settings.max_properties]
                ]
                if sent_at is None and header.get("Date"):
                    try:
                        sent_at = parsedate_to_datetime(header.get("Date"))
                    except (TypeError, ValueError, OverflowError):
                        pass
            except Exception:
                warnings.append("Encabezados de transporte parcialmente ilegibles.")
        for key, label in (
            ("classType", "Clase"),
            ("importance", "Importancia"),
            ("stringEncoding", "Codificación"),
            ("messageId", "Message-ID"),
        ):
            value = _text(_read_attribute(message, key, warnings))
            if value:
                properties.insert(0, MetadataItem(group="Mensaje", label=label, value=value))
        properties.extend(_fixed_properties(message, warnings))
        attachments = _extract_attachments(message, warnings, attachment_info, started + 30)
        if any(item.warnings for item in attachments):
            warnings.append("Uno o más adjuntos tienen advertencias; consulta la pestaña Adjuntos.")
        return _limit_response(
            MessageMetadata(
                file_name=original_name,
                file_size_bytes=size_bytes,
                subject=subject,
                sender=sender,
                recipients=recipients,
                sent_at=sent_at,
                received_at=received_at,
                body_preview=body[: settings.max_body_chars] if body else None,
                body_truncated=truncated,
                properties=properties,
                headers=headers,
                attachments=attachments,
                warnings=warnings,
                status="partial" if warnings else "complete",
            )
        )
    finally:
        try:
            message.close()
        except Exception:
            # El proceso finaliza y el SO libera handles; no perder el resultado recuperado.
            pass
