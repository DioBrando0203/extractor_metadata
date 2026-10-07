"""Correos adjuntos como archivo: ``.eml`` y ``.msg`` con sus bytes (PEN-01)."""

import io
from dataclasses import replace
from email.message import EmailMessage

import pytest
from fastapi.testclient import TestClient
from msg_factory import build_cfb, make_msg, message_streams
from PIL import Image

from app.api.routes import messages
from app.main import app
from app.services.msg import extract_msg_file

PDF = b"%PDF-1.4\nprecio del acero\n%%EOF"
NESTED_PDF = b"%PDF-1.4\npedido interno\n%%EOF"


def _png() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (40, 20), (200, 30, 30)).save(buffer, "PNG")
    return buffer.getvalue()


def _eml() -> bytes:
    """EML con texto y HTML, logo incrustado, un PDF y otro correo adjunto con su PDF."""
    inner = EmailMessage()
    inner["From"] = "Compras <compras@example.test>"
    inner["Subject"] = "Pedido interno"
    inner.set_content("Texto del pedido interno.")
    inner.add_attachment(NESTED_PDF, maintype="application", subtype="pdf", filename="pedido.pdf")

    outer = EmailMessage()
    outer["From"] = "Proveedor <ventas@acero.example.test>"
    outer["To"] = "Ana <ana@example.test>, compras@example.test"
    outer["Cc"] = "copia@example.test"
    outer["Subject"] = "Cotización de acero"
    outer["Date"] = "Mon, 05 Oct 2026 10:00:00 -0500"
    outer.set_content("Texto plano del EML.")
    outer.add_alternative('<p>Hola Ana</p><img src="cid:logo@acero"><p>Saludos</p>', subtype="html")
    html = outer.get_payload()[1]
    html.add_related(
        _png(), maintype="image", subtype="png", cid="<logo@acero>", filename="logo.png"
    )
    outer.add_attachment(PDF, maintype="application", subtype="pdf", filename="precio.pdf")
    outer.add_attachment(inner)
    return bytes(outer)


def _with_file(name: str, payload: bytes) -> bytes:
    return build_cfb(
        message_streams(body="Te reenvío el archivo.", attachment=payload, filename=name)
    )


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


def test_eml_attachment_is_read_like_an_email(tmp_path):
    attachment = _extract(tmp_path, _with_file("cotizacion.eml", _eml())).attachments[0]

    assert (attachment.kind, attachment.content_type) == ("message", "message/rfc822")
    inner = attachment.message
    assert inner.subject == "Cotización de acero"
    assert inner.sender == "Proveedor <ventas@acero.example.test>"
    assert inner.recipients == [
        "Para: Ana <ana@example.test>; compras@example.test",
        "CC: copia@example.test",
    ]
    assert inner.sent_at.isoformat() == "2026-10-05T10:00:00-05:00"
    assert "[cid:logo@acero]" in inner.body_preview
    names = [item.name for item in inner.attachments]
    assert names == ["logo.png", "precio.pdf", "Pedido interno"]
    logo, pdf, nested = inner.attachments
    assert logo.content_id == "logo@acero"
    assert logo.preview is not None
    assert pdf.size_bytes == len(PDF)
    assert nested.kind == "message"
    assert nested.message.body_preview == "Texto del pedido interno."
    assert nested.message.attachments[0].name == "pedido.pdf"


def test_attachments_inside_an_eml_download_through_the_message_path(client):
    data = _with_file("cotizacion.eml", _eml())

    def download(index: str, path: str):
        return client.post(
            "/api/messages/attachment",
            data={"attachment_index": index, "message_path": path},
            files={"file": ("correo.msg", data)},
        )

    pdf = download("1", "0")
    assert pdf.status_code == 200, pdf.text
    assert pdf.content == PDF
    nested_pdf = download("0", "0/2")
    assert nested_pdf.status_code == 200, nested_pdf.text
    assert nested_pdf.content == NESTED_PDF
    nested = download("2", "0")
    assert nested.headers["content-type"].startswith("message/rfc822")
    assert b"Subject: Pedido interno" in nested.content
    assert download("0", "0/0").status_code == 422


def test_msg_attached_as_a_file_is_read_and_its_attachments_download(client, tmp_path_factory):
    forwarded = make_msg(subject="Acta de obra", attachment=PDF, filename="acta.pdf")
    data = _with_file("Acta de obra.msg", forwarded)

    attachment = _extract(tmp_path_factory.mktemp("analisis"), data).attachments[0]
    assert attachment.kind == "message"
    assert attachment.message.subject == "Acta de obra"
    assert attachment.message.attachments[0].name == "acta.pdf"
    response = client.post(
        "/api/messages/attachment",
        data={"attachment_index": "0", "message_path": "0"},
        files={"file": ("correo.msg", data)},
    )
    assert response.status_code == 200, response.text
    assert response.content == PDF


def test_files_that_only_look_like_messages_stay_files(tmp_path):
    word = build_cfb({("WordDocument",): b"documento" * 600})
    not_mail = b"Notas sueltas sin encabezados de correo."

    doc = _extract(tmp_path, _with_file("acta.doc", word)).attachments[0]
    text = _extract(tmp_path, _with_file("notas.eml", not_mail)).attachments[0]

    assert (doc.kind, doc.message) == ("file", None)
    assert (text.kind, text.message) == ("file", None)
