import io
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace

import pytest
from fastapi.testclient import TestClient
from msg_factory import build_cfb, make_msg

from app.api.routes import messages
from app.core import middleware
from app.core.errors import ExtractionError
from app.main import app
from app.models.schemas import MessageMetadata, MetadataItem
from app.services import message_extractor
from app.services.message_extractor import extract_msg_file


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(messages, "settings", replace(messages.settings, temp_root=tmp_path))
    with TestClient(app, base_url="http://localhost") as local_client:
        yield local_client
    assert list(tmp_path.iterdir()) == []


def test_actual_msg_extraction_and_cleanup(client):
    response = client.post("/api/messages/extract", files={"file": ("correo.msg", make_msg())})
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["processed_locally"] is True
    assert data["message"]["subject"] == "Mensaje de prueba — áéíóú"
    assert "equipo@example.test" in data["message"]["sender"]
    assert data["message"]["body_preview"] == "Contenido de prueba local."
    assert data["message"]["headers"]
    assert len(data["message"]["properties"]) > 5


def test_reject_wrong_extension(client):
    response = client.post("/api/messages/extract", files={"file": ("fake.pdf", b"no msg")})
    assert response.status_code == 415


def test_corrupt_msg_has_actionable_error(client):
    response = client.post("/api/messages/extract", files={"file": ("roto.msg", b"not ole")})
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "INVALID_OR_CORRUPT_MSG"


def test_generic_ole_is_not_msg(tmp_path):
    path = tmp_path / "fake.msg"
    path.write_bytes(build_cfb({("Unrelated",): b"not a message"}))
    with pytest.raises(ExtractionError, match="no contiene"):
        extract_msg_file(path, path.name, path.stat().st_size)


def test_recover_text_when_primary_parser_fails(tmp_path, monkeypatch):
    path = tmp_path / "recuperar.msg"
    path.write_bytes(make_msg())

    def fail(*args, **kwargs):
        raise ValueError("parser roto")

    monkeypatch.setattr(message_extractor.extract_msg, "openMsg", fail)
    result = extract_msg_file(path, path.name, path.stat().st_size)
    assert result.status == "partial"
    assert result.subject == "Mensaje de prueba — áéíóú"
    assert "recuperaron" in " ".join(result.warnings)


def test_large_msg_and_attachment_are_processed(client):
    attachment = b"AC1032" + b"0" * (11 * 1024 * 1024)
    response = client.post(
        "/api/messages/extract",
        files={"file": ("archivo_grande.msg", make_msg(attachment=attachment))},
    )
    assert response.status_code == 200, response.text
    message = response.json()["message"]
    assert message["file_size_bytes"] > 10 * 1024 * 1024
    assert message["attachments"][0]["size_bytes"] == len(attachment)
    assert "10 MB" in " ".join(message["attachments"][0]["warnings"])
    assert message["status"] == "partial"


def test_windows_path_does_not_become_output_path(client):
    response = client.post(
        "/api/messages/extract", files={"file": (r"C:\folder\sub\correo.msg", make_msg())}
    )
    assert response.status_code == 200
    assert response.json()["message"]["file_name"] == "correo.msg"


def test_truncated_body_is_explicit(tmp_path):
    path = tmp_path / "largo.msg"
    path.write_bytes(make_msg(body="a" * 110_000))
    message = extract_msg_file(path, "largo.msg", path.stat().st_size)
    assert message.body_truncated is True
    assert len(message.body_preview) == 100_000
    assert len(message.model_dump_json()) < 200_000


def test_upload_limit_and_cleanup(client, monkeypatch):
    monkeypatch.setattr(messages, "settings", replace(messages.settings, max_upload_bytes=10))
    response = client.post("/api/messages/extract", files={"file": ("grande.msg", b"x" * 11)})
    assert response.status_code == 413


def test_foreign_origin_cannot_upload(client):
    response = client.post(
        "/api/messages/extract",
        headers={"Origin": "https://external.test"},
        files={"file": ("correo.msg", make_msg())},
    )
    assert response.status_code == 403


def test_reject_rebound_host(client):
    assert client.get("/api/health", headers={"Host": "external.test"}).status_code == 400


def test_health_does_not_block_during_extraction(client, monkeypatch):
    started = threading.Event()
    finish = threading.Event()

    def wait_for_finish(path, filename, size):
        started.set()
        assert finish.wait(timeout=4)
        return MessageMetadata(file_name=filename, file_size_bytes=size)

    monkeypatch.setattr(messages, "run_extraction", wait_for_finish)
    with ThreadPoolExecutor() as pool:
        upload = pool.submit(
            client.post, "/api/messages/extract", files={"file": ("local.msg", make_msg())}
        )
        try:
            assert started.wait(timeout=2)
            assert client.get("/api/health").status_code == 200
        finally:
            finish.set()
        assert upload.result(timeout=3).status_code == 200


def test_multipart_limit_applies_without_content_length(client, monkeypatch):
    monkeypatch.setattr(middleware, "settings", replace(middleware.settings, max_upload_bytes=1))
    chunk = b'--boundary\r\nContent-Disposition: form-data; name="file"; filename="x.msg"\r\n\r\n'
    response = client.post(
        "/api/messages/extract",
        content=iter([chunk, b"a" * (1024 * 1024 + 20)]),
        headers={"Content-Type": "multipart/form-data; boundary=boundary"},
    )
    assert response.status_code == 413


def test_metadata_budget_is_explicit(monkeypatch):
    monkeypatch.setattr(
        message_extractor,
        "settings",
        replace(message_extractor.settings, max_total_metadata_chars=20),
    )
    message = MessageMetadata(
        file_name="x.msg",
        file_size_bytes=1,
        properties=[MetadataItem(group="Test", label="Nombre", value="x" * 100)],
    )
    result = message_extractor._limit_response(message)
    assert result.properties == []
    assert result.status == "partial"
    assert "límite total" in result.warnings[0]


@pytest.mark.parametrize("kind", ["image", "pdf", "xlsx", "dxf"])
def test_native_metadata_inside_real_msg_worker(client, kind):
    output = io.BytesIO()
    if kind == "image":
        from PIL import Image

        Image.new("RGB", (10, 8)).save(output, format="PNG")
        payload, filename, label = output.getvalue(), "foto.png", "Dimensiones"
    elif kind == "pdf":
        from pypdf import PdfWriter

        writer = PdfWriter()
        writer.add_blank_page(100, 100)
        writer.write(output)
        payload, filename, label = output.getvalue(), "doc.pdf", "Páginas"
    elif kind == "xlsx":
        from openpyxl import Workbook

        book = Workbook()
        book.active.title = "Datos"
        book.save(output)
        book.close()
        payload, filename, label = output.getvalue(), "datos.xlsx", "Hojas"
    else:
        import ezdxf

        text = io.StringIO()
        ezdxf.new().write(text)
        payload, filename, label = text.getvalue().encode("utf8"), "plano.dxf", "Capas"
    response = client.post(
        "/api/messages/extract",
        files={"file": ("adjunto.msg", make_msg(attachment=payload, filename=filename))},
    )
    assert response.status_code == 200, response.text
    metadata = response.json()["message"]["attachments"][0]["metadata"]
    assert label in {item["label"] for item in metadata}


def test_broken_optional_ole_stream_does_not_discard_readable_message(tmp_path, monkeypatch):
    path = tmp_path / "parcial.msg"
    path.write_bytes(make_msg(extra_streams={("__substg1.0_6666001F",): b"broken"}))
    original = message_extractor.olefile.OleFileIO.openstream

    def open_without_bad_stream(self, filename):
        if filename == ["__substg1.0_6666001F"]:
            raise OSError("stream defectuoso")
        return original(self, filename)

    monkeypatch.setattr(message_extractor.olefile.OleFileIO, "openstream", open_without_bad_stream)
    result = extract_msg_file(path, path.name, path.stat().st_size)
    assert result.subject == "Mensaje de prueba — áéíóú"
    assert result.status == "partial"
    assert any("Stream OLE ilegible" in warning for warning in result.warnings)


def test_attachment_size_is_checked_before_loading_payload(tmp_path, monkeypatch):
    path = tmp_path / "limite.msg"
    path.write_bytes(make_msg(attachment=b"AC1032" + b"0" * 100))
    monkeypatch.setattr(
        message_extractor, "settings", replace(message_extractor.settings, max_attachment_bytes=10)
    )
    result = extract_msg_file(path, path.name, path.stat().st_size)
    assert result.attachments[0].size_bytes == 106
    assert result.attachments[0].name == "plano.dwg"
    assert "antes de cargarlo" in result.attachments[0].warnings[0]
