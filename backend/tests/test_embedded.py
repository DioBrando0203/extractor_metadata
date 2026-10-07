"""Correos adjuntos (PEN-01) y adjuntos por referencia a la nube o a una ruta (PEN-02)."""

from dataclasses import replace

import pytest
from fastapi.testclient import TestClient
from msg_factory import attached_message, build_cfb, message_streams, reference_attachment

from app.api.routes import messages
from app.main import app
from app.models.schemas import AttachmentMetadata, MessageMetadata
from app.services.msg import embedded, extract_msg_file, limits, reader

PDF = b"%PDF-1.4\ncontenido del correo interno\n%%EOF"
FIRST = "__attach_version1.0_#00000000"
SECOND = "__attach_version1.0_#00000001"
CLOUD_URL = "https://contoso.sharepoint.com/:x:/r/sites/obra/Presupuesto.xlsx"


def _inner() -> dict[tuple[str, ...], bytes]:
    return message_streams(
        subject="Cotización interna",
        sender="proveedor@example.test",
        body="Texto del correo reenviado.",
        attachment=PDF,
        filename="informe.pdf",
    )


def _forwarded(display_name: str | None = "Cotización interna") -> bytes:
    streams = attached_message(FIRST, _inner(), display_name)
    return build_cfb(message_streams(body="Te reenvío el correo.", extra_streams=streams))


def _extract(tmp_path, data: bytes) -> MessageMetadata:
    path = tmp_path / "correo.msg"
    path.write_bytes(data)
    return extract_msg_file(path, path.name, len(data))


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(messages, "settings", replace(messages.settings, temp_root=tmp_path))
    with TestClient(app, base_url="http://localhost") as local_client:
        yield local_client
    assert list(tmp_path.iterdir()) == []


def test_attached_message_is_read_like_its_own_email(client):
    response = client.post("/api/messages/extract", files={"file": ("reenvio.msg", _forwarded())})

    assert response.status_code == 200, response.text
    [attachment] = response.json()["message"]["attachments"]
    assert attachment["kind"] == "message"
    assert attachment["name"] == "Cotización interna"
    assert attachment["size_bytes"] > 0
    assert attachment["warnings"] == []
    inner = attachment["message"]
    assert inner["subject"] == "Cotización interna"
    assert "proveedor@example.test" in inner["sender"]
    assert inner["body_preview"] == "Texto del correo reenviado."
    assert [item["name"] for item in inner["attachments"]] == ["informe.pdf"]


def test_inner_attachment_downloads_through_the_message_path(client):
    response = client.post(
        "/api/messages/attachment",
        data={"attachment_index": "0", "message_path": "0"},
        files={"file": ("reenvio.msg", _forwarded())},
    )

    assert response.status_code == 200, response.text
    assert response.content == PDF
    assert "informe.pdf" in response.headers["content-disposition"]


def test_attached_message_downloads_as_a_readable_msg(client, tmp_path_factory):
    response = client.post(
        "/api/messages/attachment",
        data={"attachment_index": "0"},
        files={"file": ("reenvio.msg", _forwarded())},
    )

    assert response.status_code == 200, response.text
    assert response.headers["content-type"].startswith("application/vnd.ms-outlook")
    assert "Cotizaci" in response.headers["content-disposition"]
    assert ".msg" in response.headers["content-disposition"]
    copy = _extract(tmp_path_factory.mktemp("descarga"), response.content)
    assert copy.subject == "Cotización interna"
    assert copy.attachments[0].name == "informe.pdf"


@pytest.mark.parametrize("message_path", ["x", "0/", "1/2/3/4"])
def test_invalid_message_path_is_rejected(client, message_path):
    response = client.post(
        "/api/messages/attachment",
        data={"attachment_index": "0", "message_path": message_path},
        files={"file": ("reenvio.msg", _forwarded())},
    )

    assert response.status_code == 422


def test_message_path_must_point_to_an_attached_message(client):
    plain = build_cfb(message_streams(attachment=PDF, filename="informe.pdf"))
    response = client.post(
        "/api/messages/attachment",
        data={"attachment_index": "0", "message_path": "0"},
        files={"file": ("correo.msg", plain)},
    )

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "ATTACHMENT_NOT_FOUND"


def test_unnamed_attached_message_takes_its_subject_as_name(tmp_path):
    result = _extract(tmp_path, _forwarded(display_name=None))

    assert result.attachments[0].name == "Cotización interna"
    assert result.attachments[0].message.file_name == "adjunto-1.msg"


def test_message_inside_a_message_inside_a_message(tmp_path):
    deepest = message_streams(subject="Nivel 2", body="Lo más profundo.")
    middle = message_streams(subject="Nivel 1", extra_streams=attached_message(FIRST, deepest))
    result = _extract(
        tmp_path, build_cfb(message_streams(extra_streams=attached_message(FIRST, middle)))
    )

    level_1 = result.attachments[0].message
    level_2 = level_1.attachments[0].message
    assert (level_1.subject, level_2.subject) == ("Nivel 1", "Nivel 2")
    assert level_2.body_preview == "Lo más profundo."
    assert [path.name for path in tmp_path.iterdir()] == ["correo.msg"]


def test_nesting_stops_at_the_depth_limit(tmp_path, monkeypatch):
    monkeypatch.setattr(embedded, "settings", replace(embedded.settings, max_embedded_depth=1))
    deepest = message_streams(subject="Nivel 2")
    middle = message_streams(subject="Nivel 1", extra_streams=attached_message(FIRST, deepest))
    result = _extract(
        tmp_path, build_cfb(message_streams(extra_streams=attached_message(FIRST, middle)))
    )

    level_1 = result.attachments[0]
    assert level_1.message.subject == "Nivel 1"
    level_2 = level_1.message.attachments[0]
    assert level_2.kind == "message"
    assert level_2.message is None
    assert "niveles" in level_2.warnings[0]
    assert [path.name for path in tmp_path.iterdir()] == ["correo.msg"]


def test_attached_messages_are_limited_per_analysis(tmp_path, monkeypatch):
    monkeypatch.setattr(embedded, "settings", replace(embedded.settings, max_embedded_messages=1))
    streams = attached_message(FIRST, message_streams(subject="Primero"))
    streams.update(attached_message(SECOND, message_streams(subject="Segundo")))
    result = _extract(tmp_path, build_cfb(message_streams(extra_streams=streams)))

    opened = [
        attachment.message.subject if attachment.message else None
        for attachment in result.attachments
    ]
    assert opened == ["Primero", None]
    assert result.attachments[1].warnings


def test_attached_message_is_opened_when_the_parser_fails(tmp_path, monkeypatch):
    def fail(*args, **kwargs):
        raise RuntimeError("parser no disponible")

    monkeypatch.setattr(reader.extract_msg, "openMsg", fail)
    result = _extract(tmp_path, _forwarded())

    inner = result.attachments[0].message
    assert inner.subject == "Cotización interna"
    assert inner.attachments[0].name == "informe.pdf"
    assert inner.attachments[0].size_bytes == len(PDF)


def test_damaged_stream_inside_the_attached_message_is_reported(tmp_path, monkeypatch):
    original = embedded.olefile.OleFileIO.openstream

    def openstream(self, path):
        parts = path if isinstance(path, list) else str(path).split("/")
        if "__substg1.0_3701000D" in parts and parts[-1] == "__substg1.0_1000001F":
            raise OSError("sector dañado")
        return original(self, path)

    monkeypatch.setattr(embedded.olefile.OleFileIO, "openstream", openstream)
    inner = _extract(tmp_path, _forwarded()).attachments[0].message

    assert inner.subject == "Cotización interna"
    assert inner.status == "partial"
    assert any("dañada" in warning for warning in inner.warnings)


def test_cloud_attachment_is_a_link_without_bytes(client):
    data = build_cfb(
        message_streams(extra_streams=reference_attachment(FIRST, "Presupuesto.xlsx", CLOUD_URL))
    )
    response = client.post("/api/messages/extract", files={"file": ("correo.msg", data)})

    assert response.status_code == 200, response.text
    [attachment] = response.json()["message"]["attachments"]
    assert attachment["kind"] == "link"
    assert attachment["link"] == CLOUD_URL
    assert attachment["name"] == "Presupuesto.xlsx"
    assert attachment["size_bytes"] is None
    assert attachment["warnings"] == []
    download = client.post(
        "/api/messages/attachment",
        data={"attachment_index": "0"},
        files={"file": ("correo.msg", data)},
    )
    assert download.status_code == 422
    assert download.json()["detail"]["code"] == "UNREADABLE_ATTACHMENT"


def test_reference_to_a_network_path_and_reference_without_address(tmp_path):
    streams = reference_attachment(FIRST, "plano.dwg", r"\\servidor\obras\plano.dwg", method=2)
    streams.update(reference_attachment(SECOND, "acta.pdf", None))
    network, broken = _extract(
        tmp_path, build_cfb(message_streams(extra_streams=streams))
    ).attachments

    assert (network.kind, network.link) == ("link", r"\\servidor\obras\plano.dwg")
    assert network.metadata[0].value == r"\\servidor\obras\plano.dwg"
    assert (broken.kind, broken.link) == ("link", None)
    assert broken.warnings


def test_one_preview_budget_covers_attached_messages(monkeypatch):
    preview = "data:image/jpeg;base64,AAAA"
    monkeypatch.setattr(
        limits, "settings", replace(limits.settings, max_total_preview_chars=len(preview))
    )
    inner = MessageMetadata(
        file_name="interno.msg",
        file_size_bytes=1,
        attachments=[AttachmentMetadata(name="b.jpg", preview=preview, preview_source="image")],
    )
    outer = MessageMetadata(
        file_name="correo.msg",
        file_size_bytes=1,
        attachments=[
            AttachmentMetadata(name="a.jpg", preview=preview, preview_source="image"),
            AttachmentMetadata(name="Interno", kind="message", message=inner),
        ],
    )

    limits.limit_response(outer)

    assert outer.attachments[0].preview == preview
    assert inner.attachments[0].preview is None
