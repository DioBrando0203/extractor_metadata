"""Metadatos de Office Open XML leyendo sólo partes docProps con límites contra bombas ZIP."""

import zipfile
from io import BytesIO
from xml.etree import ElementTree

from app.services.metadata.results import DetectedFile, ExtractionResult, add_item, limited

MAX_ARCHIVE_MEMBERS = 2_000


MAX_ARCHIVE_UNCOMPRESSED_BYTES = 128 * 1024 * 1024


MAX_ARCHIVE_MEMBER_BYTES = 32 * 1024 * 1024


MAX_ARCHIVE_COMPRESSION_RATIO = 200


MAX_OFFICE_XML_BYTES = 2 * 1024 * 1024


class UnsafeOfficeArchive(ValueError):
    """ZIP Office cuya descompresión no es segura para el proceso local."""


def _validate_office_archive(archive: zipfile.ZipFile) -> None:
    infos = archive.infolist()
    if len(infos) > MAX_ARCHIVE_MEMBERS:
        raise UnsafeOfficeArchive("demasiados elementos ZIP")
    total = 0
    for info in infos:
        if info.file_size > MAX_ARCHIVE_MEMBER_BYTES:
            raise UnsafeOfficeArchive("un componente ZIP excede el límite")
        total += info.file_size
        if total > MAX_ARCHIVE_UNCOMPRESSED_BYTES:
            raise UnsafeOfficeArchive("el total ZIP descomprimido excede el límite")
        if info.file_size and (
            not info.compress_size
            or info.file_size / info.compress_size > MAX_ARCHIVE_COMPRESSION_RATIO
        ):
            raise UnsafeOfficeArchive("relación de compresión sospechosa")


def _read_office_part(archive: zipfile.ZipFile, name: str) -> bytes | None:
    try:
        info = archive.getinfo(name)
    except KeyError:
        return None
    if info.file_size > MAX_OFFICE_XML_BYTES:
        raise UnsafeOfficeArchive(f"{name} excede el límite XML")
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


def _core_properties(root: ElementTree.Element | None, result: ExtractionResult) -> None:
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
            add_item(result, "Office", labels.get(key, key), value)


def office_metadata(payload: bytes, detected: DetectedFile) -> ExtractionResult:
    result = ExtractionResult()
    try:
        with zipfile.ZipFile(BytesIO(payload)) as archive:
            _validate_office_archive(archive)
            _core_properties(_xml_root(_read_office_part(archive, "docProps/core.xml")), result)
            app_root = _xml_root(_read_office_part(archive, "docProps/app.xml"))
            if app_root is not None:
                for element in app_root:
                    value = (element.text or "").strip()
                    if value:
                        add_item(result, "Office / aplicación", _local_name(element.tag), value)
            custom_root = _xml_root(_read_office_part(archive, "docProps/custom.xml"))
            if custom_root is not None:
                for prop in custom_root:
                    value = " ".join(text.strip() for text in prop.itertext() if text.strip())
                    if value:
                        add_item(
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
                    add_item(result, "Excel", "Cantidad de hojas", len(sheets))
                    if sheets:
                        add_item(result, "Excel", "Hojas", ", ".join(sheets))
            elif detected.kind == "docx":
                add_item(result, "Office", "Formato", "Word Open XML")
            else:
                add_item(result, "Office", "Formato", "PowerPoint Open XML")
    except UnsafeOfficeArchive as error:
        result.warnings.append(f"No se inspeccionó Office: {error}.")
    except (OSError, zipfile.BadZipFile):
        result.warnings.append(
            "No se pudieron leer los metadatos Office; el contenedor ZIP está dañado."
        )
    return limited(result, "Office")
