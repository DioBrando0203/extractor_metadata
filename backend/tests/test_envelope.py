"""Identificación del remitente, asunto, destinatarios y fecha, e imágenes en su posición."""

from __future__ import annotations

import io

from msg_factory import make_msg
from PIL import Image

from app.services.body_text import html_to_text
from app.services.msg import extract_msg_file, reader
from app.services.msg.envelope import Envelope, envelope_from_headers, envelope_from_properties

HEADERS = (
    "From: =?utf-8?Q?Mar=C3=ADa_Fern=C3=A1ndez?= <maria@example.test>\r\n"
    'To: "Rojas, Carlos" <carlos@example.test>, equipo@example.test\r\n'
    "Cc: Ana <ana@example.test>\r\n"
    "Subject: =?utf-8?B?UkU6IFJldmlzacOzbiBkZSBwbGFub3M=?=\r\n"
    "Date: Mon, 05 Oct 2026 10:00:00 -0500\r\n"
)


def _png() -> bytes:
    output = io.BytesIO()
    Image.new("RGB", (8, 8), (10, 120, 200)).save(output, "PNG")
    return output.getvalue()


def test_headers_give_sender_subject_recipients_and_date():
    envelope = envelope_from_headers(HEADERS)
    assert envelope.sender == "María Fernández <maria@example.test>"
    assert envelope.subject == "RE: Revisión de planos"
    assert envelope.recipients == [
        "Para: Rojas, Carlos <carlos@example.test>; equipo@example.test",
        "CC: Ana <ana@example.test>",
    ]
    assert envelope.sent_at is not None and envelope.sent_at.year == 2026


def test_properties_prefer_smtp_and_skip_exchange_addresses():
    envelope = envelope_from_properties(
        {
            "0C1A": "María",
            "0C1F": "/O=EXCHANGELABS/OU=GRUPO/CN=MARIA",
            "5D01": "maria@example.test",
            "0E1D": "Revisión",
            "003D": "RE: ",
        }
    )
    assert envelope.sender == "María <maria@example.test>"
    assert envelope.subject == "RE: Revisión"


def test_envelope_fills_only_missing_fields_in_order():
    envelope = Envelope(subject="Original").complete_with(
        Envelope(subject="Respaldo", sender="primero@example.test"),
        Envelope(sender="segundo@example.test", recipients=["Para: x@example.test"]),
    )
    assert envelope == Envelope(
        subject="Original",
        sender="primero@example.test",
        recipients=["Para: x@example.test"],
    )


def test_recovered_message_identifies_sender_from_transport_headers(tmp_path, monkeypatch):
    """Simula el daño real: el parser falla y las propiedades cortas del mini stream se pierden."""
    path = tmp_path / "danado.msg"
    path.write_bytes(make_msg(omit=("0037", "0C1A", "0C1F", "0E04"), headers=HEADERS))

    def fail(*_args, **_kwargs):
        raise OSError("FAT dañada")

    monkeypatch.setattr(reader.extract_msg, "openMsg", fail)
    message = extract_msg_file(path, "danado.msg", path.stat().st_size)
    assert message.status == "partial"
    assert message.subject == "RE: Revisión de planos"
    assert message.sender == "María Fernández <maria@example.test>"
    assert message.recipients[0].startswith("Para: Rojas, Carlos")
    assert message.sent_at is not None


def test_parsed_message_completes_missing_subject_from_headers(tmp_path):
    path = tmp_path / "sin-asunto.msg"
    path.write_bytes(make_msg(omit=("0037",), headers=HEADERS))
    message = extract_msg_file(path, "sin-asunto.msg", path.stat().st_size)
    assert message.subject == "RE: Revisión de planos"


def test_html_images_become_position_markers_and_remote_images_are_dropped():
    text = html_to_text(
        '<p>Hola</p><img src="cid:image001.png@01DA"><p>Firma</p><img src="https://rastreo/x.gif">'
    )
    assert [line for line in text.splitlines() if line] == [
        "Hola",
        "[cid:image001.png@01DA]",
        "Firma",
    ]
    assert "rastreo" not in text


def test_inline_image_keeps_content_id_and_position_in_body(tmp_path):
    path = tmp_path / "inline.msg"
    path.write_bytes(
        make_msg(
            body="Hola equipo",
            html='<p>Hola equipo</p><img src="cid:image001.png@01DA"><p>Saludos</p>',
            attachment=_png(),
            filename="image001.png",
            content_id="<image001.png@01DA>",
        )
    )
    message = extract_msg_file(path, "inline.msg", path.stat().st_size)
    assert message.attachments[0].content_id == "image001.png@01DA"
    assert "[cid:image001.png@01DA]" in (message.body_preview or "")
    assert message.body_preview.index("Hola") < message.body_preview.index("[cid:")
