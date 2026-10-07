"""Descargar todos los adjuntos en un ZIP (PEN-11)."""

import io
import zipfile
from dataclasses import replace

import pytest
from fastapi.testclient import TestClient
from msg_factory import (
    attached_message,
    attachment_properties,
    build_cfb,
    message_streams,
    reference_attachment,
)

from app.api.routes import messages
from app.main import app

PDF = b"%PDF-1.4\ninforme\n%%EOF"
INNER_PDF = b"%PDF-1.4\npedido interno\n%%EOF"
FOLDER = "__attach_version1.0_#{:08X}"


def _file(index: int, name: str, payload: bytes) -> dict[tuple[str, ...], bytes]:
    folder = FOLDER.format(index)
    return {
        (folder, "__properties_version1.0"): attachment_properties(1),
        (folder, "__substg1.0_3707001F"): name.encode("utf-16-le"),
        (folder, "__substg1.0_37010102"): payload,
    }


def _mail() -> bytes:
    """PDF, el mismo nombre repetido, un correo adjunto con su PDF y un enlace a la nube."""
    streams = _file(0, "informe.pdf", PDF)
    streams.update(_file(1, "Informe.pdf", b"%PDF-1.4\notro\n%%EOF"))
    inner = message_streams(subject="Pedido", attachment=INNER_PDF, filename="pedido.pdf")
    streams.update(attached_message(FOLDER.format(2), inner, "Pedido"))
    streams.update(reference_attachment(FOLDER.format(3), "Presupuesto.xlsx", "https://x.test/p"))
    return build_cfb(message_streams(extra_streams=streams))


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(messages, "settings", replace(messages.settings, temp_root=tmp_path))
    with TestClient(app, base_url="http://localhost") as local_client:
        yield local_client
    assert list(tmp_path.iterdir()) == []


def _download_all(client, data: bytes, message_path: str = ""):
    return client.post(
        "/api/messages/attachments",
        data={"message_path": message_path},
        files={"file": ("Revisión de obra.msg", data)},
    )


def test_all_attachments_come_in_one_zip_without_links(client):
    response = _download_all(client, _mail())

    assert response.status_code == 200, response.text
    assert response.headers["content-type"] == "application/zip"
    assert "adjuntos.zip" in response.headers["content-disposition"]
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        assert archive.namelist() == ["informe.pdf", "Informe (2).pdf", "Pedido.msg"]
        assert archive.read("informe.pdf") == PDF


def test_attachments_of_an_attached_message_come_with_the_message_path(client):
    response = _download_all(client, _mail(), message_path="2")

    assert response.status_code == 200, response.text
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        assert archive.namelist() == ["pedido.pdf"]
        assert archive.read("pedido.pdf") == INNER_PDF


def test_mail_with_only_links_has_nothing_to_zip(client):
    data = build_cfb(
        message_streams(
            extra_streams=reference_attachment(FOLDER.format(0), "a.xlsx", "https://x.test")
        )
    )

    response = _download_all(client, data)

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "ATTACHMENT_NOT_FOUND"


def test_download_name_is_readable_from_another_origin(client):
    response = client.post(
        "/api/messages/attachments",
        headers={"Origin": "http://127.0.0.1:5173"},
        files={"file": ("obra.msg", _mail())},
    )

    assert response.status_code == 200, response.text
    assert "content-disposition" in response.headers["access-control-expose-headers"].lower()
