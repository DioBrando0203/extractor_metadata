"""MSG con la cabecera dañada (PEN-03): firma repuesta en copia o lectura de rescate."""

import io
import os
from dataclasses import replace

import pytest
from fastapi.testclient import TestClient
from msg_factory import make_msg
from PIL import Image

from app.api.routes import messages
from app.main import app
from app.services.msg import extract_attachment_file, extract_msg_file


def _photo() -> bytes:
    """PNG que no cabe en el mini stream: vive en sectores normales y contiguos."""
    buffer = io.BytesIO()
    Image.frombytes("L", (120, 120), os.urandom(120 * 120)).save(buffer, "PNG")
    return buffer.getvalue()


def _damaged(header_bytes: int) -> tuple[bytes, bytes]:
    photo = _photo()
    data = bytearray(make_msg(attachment=photo, filename="foto.png"))
    data[:header_bytes] = bytes(header_bytes)
    return bytes(data), photo


def _extract(tmp_path, data: bytes):
    path = tmp_path / "correo.msg"
    path.write_bytes(data)
    return extract_msg_file(path, path.name, len(data))


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(messages, "settings", replace(messages.settings, temp_root=tmp_path))
    with TestClient(app, base_url="http://localhost") as local_client:
        yield local_client
    assert list(tmp_path.iterdir()) == []


def test_erased_signature_is_restored_in_a_copy(tmp_path):
    data, photo = _damaged(header_bytes=8)

    result = _extract(tmp_path, data)

    assert result.subject == "Mensaje de prueba — áéíóú"
    assert [item.name for item in result.attachments] == ["foto.png"]
    assert any("firma del archivo" in warning for warning in result.warnings)
    assert (tmp_path / "correo.msg").read_bytes()[:8] == bytes(8)
    output = tmp_path / "foto.bin"
    assert extract_attachment_file(tmp_path / "correo.msg", 0, output)[0] == "foto.png"
    assert output.read_bytes() == photo


def test_destroyed_header_still_yields_envelope_and_attachments(tmp_path):
    data, photo = _damaged(header_bytes=512)

    result = _extract(tmp_path, data)

    assert result.status == "partial"
    assert "equipo@example.test" in result.sender
    assert result.recipients == ["Para: lector@example.test"]
    assert result.sent_at.isoformat() == "2026-10-05T10:00:00-05:00"
    assert [(item.name, item.size_bytes) for item in result.attachments] == [
        ("imagen-recuperado-1.png", len(photo))
    ]
    assert "cabecera del archivo está destruida" in result.warnings[0]


def test_rescued_attachment_downloads_with_its_exact_bytes(client):
    data, photo = _damaged(header_bytes=512)

    analysis = client.post("/api/messages/extract", files={"file": ("roto.msg", data)})
    download = client.post(
        "/api/messages/attachment",
        data={"attachment_index": "0"},
        files={"file": ("roto.msg", data)},
    )

    assert analysis.status_code == 200, analysis.text
    assert analysis.json()["message"]["attachments"][0]["name"] == "imagen-recuperado-1.png"
    assert download.status_code == 200, download.text
    assert download.content == photo
    nested = client.post(
        "/api/messages/attachment",
        data={"attachment_index": "0", "message_path": "0"},
        files={"file": ("roto.msg", data)},
    )
    assert nested.status_code == 422
