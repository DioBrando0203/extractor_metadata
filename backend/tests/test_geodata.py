"""Contrato HTTP del conversor KML/KMZ efímero (PEN-15)."""

import io
import zipfile
from dataclasses import replace

import pytest
from fastapi.testclient import TestClient

from app.api.routes import geodata
from app.main import app


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


def test_geodata_reports_missing_gdal_without_leaving_a_temp(client) -> None:
    payload = b'<?xml version="1.0"?><kml xmlns="http://www.opengis.net/kml/2.2"/>'

    response = client.post("/api/geodata/convert", files={"file": ("mapa.kml", payload)})

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "GDAL_UNAVAILABLE"


def test_kmz_without_kml_is_rejected_before_starting_gdal(client) -> None:
    content = io.BytesIO()
    with zipfile.ZipFile(content, "w") as archive:
        archive.writestr("nota.txt", "sin geometría")

    response = client.post("/api/geodata/convert", files={"file": ("mapa.kmz", content.getvalue())})

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "INVALID_KMZ"
