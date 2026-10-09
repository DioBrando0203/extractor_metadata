"""MiniFAT perdida en la cabecera con el mini stream fragmentado (PEN-04)."""

import io
import os
import struct

import pytest
from msg_factory import END, SECTOR, build_cfb, message_streams
from PIL import Image

from app.core.errors import ExtractionError
from app.services.msg import extract_attachment_file, extract_msg_file
from app.services.msg.fat_recovery import recovered_ole_path
from app.services.msg.minifat_recovery import locate_minifat

SUBJECT = "Planos revisados — versión final"
#: Textos de 3 300 bytes: caben en el mini stream y lo extienden a varios sectores.
FILLERS = {f"3A{index:02X}": f"Relleno {index} " * 150 for index in range(16, 20)}


def _photo() -> bytes:
    """PNG que no cabe en el mini stream: sus bytes siguen legibles sin la MiniFAT."""
    buffer = io.BytesIO()
    Image.frombytes("L", (120, 120), os.urandom(120 * 120)).save(buffer, "PNG")
    return buffer.getvalue()


def _fragmented_msg(photo: bytes) -> bytearray:
    """Asunto, encabezados, nombre y Content-ID sólo en el mini stream, que ocupa varios sectores
    en orden inverso; el asunto queda al final, lejos del inicio de la cadena."""
    headers = f"From: equipo@example.test\r\nSubject: {SUBJECT}\r\nTo: lector@example.test\r\n"
    streams = message_streams(
        attachment=photo,
        filename="foto.png",
        content_id="foto@local",
        headers=headers,
        omit=("0037",),
        properties=FILLERS,
        extra_streams={("__substg1.0_0037001F",): SUBJECT.encode("utf-16-le")},
    )
    return bytearray(build_cfb(streams, scatter=True))


def _minifat_start(data: bytearray) -> int:
    return struct.unpack_from("<I", data, 60)[0]


def _lose_minifat(data: bytearray) -> bytes:
    struct.pack_into("<II", data, 60, END, 0)
    return bytes(data)


def test_lost_minifat_is_restored_from_a_fragmented_mini_stream(tmp_path):
    photo = _photo()
    data = _lose_minifat(_fragmented_msg(photo))
    path = tmp_path / "minifat-perdida.msg"
    path.write_bytes(data)

    result = extract_msg_file(path, path.name, len(data))

    assert result.subject == SUBJECT
    assert any(item.label == "Subject" and item.value == SUBJECT for item in result.headers)
    assert any("MiniFAT" in warning for warning in result.warnings)
    attachment = result.attachments[0]
    assert attachment.name == "foto.png"
    assert attachment.content_id == "foto@local"
    assert not attachment.content_id_inferred
    name, _ = extract_attachment_file(path, 0, tmp_path / "foto")
    assert name == "foto.png"
    assert (tmp_path / "foto").read_bytes() == photo
    assert path.read_bytes() == data


def test_minifat_that_does_not_explain_every_stream_is_not_used(tmp_path):
    data = _fragmented_msg(_photo())
    entry = (_minifat_start(data) + 1) * SECTOR
    # La primera cadena (clase de mensaje, un mini sector) pasa a pisar el segundo stream.
    struct.pack_into("<I", data, entry, 1)
    path = tmp_path / "minifat-incoherente.msg"
    path.write_bytes(_lose_minifat(data))

    assert locate_minifat(path) is None
    with recovered_ole_path(path) as (_, notices):
        assert notices == []
    # Sin una MiniFAT verificable no se lee nada del mini stream: ni asunto ni encabezados.
    with pytest.raises(ExtractionError):
        extract_msg_file(path, path.name, path.stat().st_size)


def test_two_tables_that_fit_are_ambiguous(tmp_path):
    data = _fragmented_msg(_photo())
    minifat = data[(_minifat_start(data) + 1) * SECTOR :][:SECTOR]
    copy_sector = (len(data) - SECTOR) // SECTOR
    fat_sector = struct.unpack_from("<I", data, 76)[0]
    struct.pack_into("<I", data, (fat_sector + 1) * SECTOR + copy_sector * 4, END)
    data += minifat
    path = tmp_path / "dos-minifat.msg"
    path.write_bytes(_lose_minifat(data))

    assert locate_minifat(path) is None


def test_healthy_header_is_read_from_the_original(tmp_path):
    path = tmp_path / "sano.msg"
    path.write_bytes(bytes(_fragmented_msg(_photo())))

    with recovered_ole_path(path) as (read_path, notices):
        assert read_path == path
        assert notices == []
