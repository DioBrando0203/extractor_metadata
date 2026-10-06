"""Metadatos de AutoCAD: DXF con ezdxf y DWG por firma de versión y miniatura incrustada."""

from io import StringIO

from app.services.metadata.results import DetectedFile, ExtractionResult, add_item, limited
from app.services.previews.embedded import embedded_thumbnail

DWG_VERSIONS = {
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


def dxf_metadata(payload: bytes, _: DetectedFile) -> ExtractionResult:
    result = ExtractionResult()
    try:
        import ezdxf

        document = ezdxf.read(StringIO(payload.decode("latin-1")))
        add_item(result, "AutoCAD", "Formato", document.dxfversion)
        add_item(result, "AutoCAD", "Unidades", document.header.get("$INSUNITS", "No definidas"))
        add_item(result, "AutoCAD", "Capas", len(document.layers))
        add_item(
            result,
            "AutoCAD",
            "Miniatura incrustada",
            "Sí" if embedded_thumbnail(payload, "dibujo.dxf") else "No",
        )
    except Exception:
        result.warnings.append(
            "No se pudieron leer los metadatos DXF; el archivo podría estar dañado "
            "o no ser DXF ASCII compatible."
        )
    return limited(result, "DXF")


def dwg_metadata(payload: bytes, _: DetectedFile) -> ExtractionResult:
    result = ExtractionResult()
    code = payload[:6].decode("ascii", errors="replace")
    if code in DWG_VERSIONS:
        add_item(result, "AutoCAD", "Firma DWG", code)
        add_item(result, "AutoCAD", "Versión de formato", DWG_VERSIONS[code])
    else:
        add_item(result, "AutoCAD", "Firma DWG", code or "No disponible")
        result.warnings.append("No se reconoció una firma DWG válida en el encabezado.")
    add_item(
        result,
        "AutoCAD",
        "Miniatura incrustada",
        "Sí" if embedded_thumbnail(payload, "dibujo.dwg") else "No",
    )
    result.warnings.append(
        "La extracción profunda de propiedades DWG no está disponible; "
        "se muestra sólo la firma de formato y la miniatura guardada por AutoCAD."
    )
    return result
