"""Metadatos de PDF con pypdf: páginas, información del documento y XMP. Nunca descifra."""

from io import BytesIO

from app.services.metadata.results import DetectedFile, ExtractionResult, add_item, limited


def pdf_metadata(payload: bytes, _: DetectedFile) -> ExtractionResult:
    result = ExtractionResult()
    stream = BytesIO(payload)
    reader = None
    try:
        from pypdf import PdfReader

        reader = PdfReader(stream, strict=False)
        add_item(result, "PDF", "Cifrado", "Sí" if reader.is_encrypted else "No")
        if reader.is_encrypted:
            result.warnings.append(
                "El PDF está cifrado; no se intentó descifrar ni leer su contenido."
            )
            return result
        add_item(result, "PDF", "Páginas", len(reader.pages))
        for key, value in (reader.metadata or {}).items():
            if value is not None and str(value):
                add_item(result, "PDF", str(key).lstrip("/"), value)
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
                        add_item(result, "PDF / XMP", name, value)
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
    return limited(result, "PDF")
