"""Contrato HTTP del conversor KML/KMZ efímero (PEN-15)."""

import io
import shutil
import zipfile
from dataclasses import replace

import pytest
from fastapi.testclient import TestClient

from app.api.routes import geodata
from app.core.errors import ExtractionError
from app.main import app
from app.services.kmz import converter


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(geodata, "settings", replace(geodata.settings, temp_root=tmp_path))
    with TestClient(app, base_url="http://localhost") as local_client:
        yield local_client
    assert list(tmp_path.iterdir()) == []


def test_geodata_rejects_an_unsupported_extension(client) -> None:
    response = client.post("/api/geodata/convert", files={"file": ("mapa.msg", b"bytes")})

    assert response.status_code == 415
    assert response.json()["detail"] == "Seleccione un .kml o .kmz."


@pytest.mark.skipif(shutil.which("ogr2ogr") is None, reason="GDAL no está instalado")
def test_geodata_converts_a_kml_without_leaving_a_temp(client) -> None:
    payload = (
        b'<?xml version="1.0"?><kml xmlns="http://www.opengis.net/kml/2.2"><Document>'
        b"<Placemark><name>Punto</name><Point><coordinates>-77,-12,0</coordinates></Point>"
        b"</Placemark></Document></kml>"
    )

    response = client.post("/api/geodata/convert", files={"file": ("mapa.kml", payload)})

    assert response.status_code == 200
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        assert archive.namelist() == ["mapa.gpkg"]
        assert archive.read("mapa.gpkg")[:16] == b"SQLite format 3\x00"


def test_converter_reports_missing_gdal(tmp_path, monkeypatch) -> None:
    source = tmp_path / "mapa.kml"
    source.write_text('<kml xmlns="http://www.opengis.net/kml/2.2"/>', encoding="utf-8")
    monkeypatch.setattr(converter, "_ogr2ogr_path", lambda: None)

    with pytest.raises(ExtractionError, match="GDAL no está instalado"):
        converter.convert_to_archive(source, tmp_path / "salida.zip", "mapa.kml", 1)


def test_kmz_without_kml_is_rejected_before_starting_gdal(client) -> None:
    content = io.BytesIO()
    with zipfile.ZipFile(content, "w") as archive:
        archive.writestr("nota.txt", "sin geometría")

    response = client.post("/api/geodata/convert", files={"file": ("mapa.kmz", content.getvalue())})

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "INVALID_KMZ"
