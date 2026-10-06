"""Cuerpo HTML recuperado de un RTF suelto y posición de imágenes reconstruida por sus medidas."""

from __future__ import annotations

import io

import compressed_rtf
from msg_factory import make_msg
from PIL import Image

from app.models.schemas import AttachmentMetadata, MetadataItem
from app.services.msg import extract_msg_file, reader
from app.services.msg.inline_images import InlineTag, assign_by_size, inline_tags
from app.services.msg.raw_body import recover_html_body

BODY = "Hola equipo, adjunto el plano de la obra."


def _image(width: int, height: int) -> AttachmentMetadata:
    return AttachmentMetadata(
        name="adjunto.png",
        metadata=[MetadataItem(group="Imagen", label="Dimensiones", value=f"{width} × {height}")],
    )


def _png(width: int, height: int) -> bytes:
    output = io.BytesIO()
    Image.new("RGB", (width, height), (20, 90, 160)).save(output, "PNG")
    return output.getvalue()


def _rtf_blob(text: str = BODY) -> bytes:
    rtf = (
        rb"{\rtf1\ansi\ansicpg1252\fromhtml1 \deff0{\fonttbl{\f0\fswiss Arial;}}"
        rb"{\*\htmltag19 <html>}{\*\htmltag34 <body>}{\*\htmltag64 <p>}"
        + text.encode("cp1252")
        + rb"{\*\htmltag72 </p>}"
        rb'{\*\htmltag84 <img width=40 height=20 src="cid:image001.png@01DA">}'
        rb"{\*\htmltag64 <p>}Saludos{\*\htmltag72 </p>}"
        rb"{\*\htmltag42 </body>}{\*\htmltag27 </html>}}"
    )
    return compressed_rtf.compress(rtf, compressed=True)


def test_inline_tags_keep_order_and_declared_size():
    html = (
        '<p>a</p><img src="cid:a@1" width="10" height=5>'
        '<img src="https://x/y.png"><img src=cid:b@1>'
    )
    assert inline_tags(html) == [InlineTag("a@1", 10, 5), InlineTag("b@1", None, None)]


def test_exact_size_wins_and_marks_the_content_id_as_inferred():
    attachments = [_image(279, 60), _image(355, 105)]
    tags = [InlineTag("image001.jpg@x", 279, 60), InlineTag("image002.png@x", 355, 105)]
    assert assign_by_size(attachments, tags) == 2
    assert [item.content_id for item in attachments] == ["image001.jpg@x", "image002.png@x"]
    assert all(item.content_id_inferred for item in attachments)


def test_unique_aspect_ratio_after_exact_matches():
    """Lo ya emparejado por tamaño exacto no compite en la pasada de proporción."""
    attachments = [_image(355, 105), _image(453, 134)]
    tags = [InlineTag("logo@x", 355, 105), InlineTag("firma@x", 302, 89)]
    assert assign_by_size(attachments, tags) == 2
    assert attachments[1].content_id == "firma@x"


def test_ambiguous_candidates_are_left_without_position():
    attachments = [_image(32, 32), _image(32, 32), _image(1294, 970), _image(1315, 978)]
    tags = [
        InlineTag("icono-1@x", 14, 14),
        InlineTag("icono-2@x", 14, 14),
        InlineTag("captura-1@x", 862, 645),
        InlineTag("captura-2@x", 876, 651),
    ]
    assert assign_by_size(attachments, tags) == 0
    assert not any(item.content_id for item in attachments)


def test_existing_content_ids_are_never_replaced():
    attachments = [_image(40, 20)]
    attachments[0].content_id = "original@x"
    assert assign_by_size(attachments, [InlineTag("otro@x", 40, 20)]) == 0
    assert attachments[0].content_id == "original@x"


def test_loose_rtf_is_recovered_only_if_it_matches_the_readable_body(tmp_path):
    path = tmp_path / "suelto.msg"
    path.write_bytes(make_msg(body=BODY, extra_streams={("__substg1.0_99990102",): _rtf_blob()}))
    assert "cid:image001.png@01DA" in recover_html_body(path, BODY)
    assert recover_html_body(path, "Un cuerpo completamente distinto del recuperado") is None


def test_corrupted_rtf_is_ignored(tmp_path):
    blob = bytearray(_rtf_blob())
    blob[-1] ^= 0xFF  # rompe el CRC
    path = tmp_path / "crc.msg"
    path.write_bytes(make_msg(body=BODY, extra_streams={("__substg1.0_99990102",): bytes(blob)}))
    assert recover_html_body(path, BODY) is None


def test_damaged_message_gets_images_back_in_position(tmp_path, monkeypatch):
    path = tmp_path / "danado.msg"
    path.write_bytes(
        make_msg(
            body=BODY,
            attachment=_png(40, 20),
            filename="adjunto.png",
            extra_streams={("__substg1.0_99990102",): _rtf_blob()},
        )
    )

    def fail(*_args, **_kwargs):
        raise OSError("FAT dañada")

    monkeypatch.setattr(reader.extract_msg, "openMsg", fail)
    message = extract_msg_file(path, "danado.msg", path.stat().st_size)
    assert "[cid:image001.png@01DA]" in (message.body_preview or "")
    assert message.attachments[0].content_id == "image001.png@01DA"
    assert message.attachments[0].content_id_inferred is True
