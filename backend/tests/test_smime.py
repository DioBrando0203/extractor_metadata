"""Correos firmados o cifrados con S/MIME (PEN-06)."""

from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from msg_factory import make_msg

from app.services.msg import extract_attachment_file, extract_msg_file, reader

PDF = b"%PDF-1.4\ncontrato firmado\n%%EOF"
SIGNED_DATA = bytes.fromhex("3080") + bytes.fromhex("06092A864886F70D010702") + b"\x00" * 40
ENVELOPED_DATA = bytes.fromhex("3080") + bytes.fromhex("06092A864886F70D010703") + b"\x00" * 40


def _clear_signed() -> bytes:
    """``multipart/signed`` como lo guarda Outlook: contenido y firma (falsa, no se verifica)."""
    content = MIMEMultipart("mixed")
    content.attach(MIMEText("Texto firmado del contrato.", "plain", "utf-8"))
    content.attach(MIMEApplication(PDF, "pdf", Name="contrato.pdf"))
    content.get_payload()[1].add_header(
        "Content-Disposition", "attachment", filename="contrato.pdf"
    )
    signature = MIMEApplication(b"firma", "pkcs7-signature", Name="smime.p7s")
    signed = MIMEMultipart("signed", protocol="application/pkcs7-signature", micalg="sha-256")
    signed.attach(content)
    signed.attach(signature)
    return signed.as_bytes()


def _smime_msg(message_class: str, payload: bytes) -> bytes:
    return make_msg(
        message_class=message_class, attachment=payload, filename="smime.p7m", omit=("1000",)
    )


def _extract(tmp_path, data: bytes):
    path = tmp_path / "firmado.msg"
    path.write_bytes(data)
    return path, extract_msg_file(path, path.name, len(data))


def test_clear_signed_mail_shows_its_content_and_real_attachments(tmp_path):
    path, result = _extract(tmp_path, _smime_msg("IPM.Note.SMIME.MultipartSigned", _clear_signed()))

    assert result.security == "signed"
    assert result.body_preview == "Texto firmado del contrato."
    assert [item.name for item in result.attachments] == ["contrato.pdf"]
    output = tmp_path / "contrato.bin"
    assert extract_attachment_file(path, 0, output) == ("contrato.pdf", "application/pdf")
    assert output.read_bytes() == PDF


def test_clear_signed_content_is_shown_even_if_the_parser_fails(tmp_path, monkeypatch):
    def fail(*args, **kwargs):
        raise RuntimeError("parser no disponible")

    monkeypatch.setattr(reader.extract_msg, "openMsg", fail)
    _, result = _extract(tmp_path, _smime_msg("IPM.Note.SMIME.MultipartSigned", _clear_signed()))

    assert (result.security, result.body_preview) == ("signed", "Texto firmado del contrato.")
    assert [item.name for item in result.attachments] == ["contrato.pdf"]


def test_encrypted_and_opaque_signed_mail_are_reported_and_keep_the_p7m(tmp_path):
    _, encrypted = _extract(tmp_path, _smime_msg("IPM.Note.SMIME", ENVELOPED_DATA))
    _, opaque = _extract(tmp_path, _smime_msg("IPM.Note.SMIME", SIGNED_DATA))

    assert (encrypted.security, encrypted.body_preview) == ("encrypted", None)
    assert [item.name for item in encrypted.attachments] == ["smime.p7m"]
    assert (opaque.security, opaque.body_preview) == ("opaque", None)
    assert [item.name for item in opaque.attachments] == ["smime.p7m"]


def test_ordinary_mail_is_not_smime(tmp_path):
    assert _extract(tmp_path, make_msg())[1].security is None


def test_rights_protected_mail_is_reported(tmp_path):
    data = make_msg(
        message_class="IPM.Note.rpmsg.Microsoft",
        attachment=b"contenido protegido",
        filename="message.rpmsg",
    )

    _, result = _extract(tmp_path, data)

    assert result.security == "protected"
    assert [item.name for item in result.attachments] == ["message.rpmsg"]
