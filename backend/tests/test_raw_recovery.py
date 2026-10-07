"""Rescate de archivos sueltos (PEN-03): formatos, exclusiones y cuándo se activa."""

import io
import struct
import zipfile

import olefile
from msg_factory import SECTOR, make_msg
from PIL import Image

from app.services.msg import extract_msg_file, reader
from app.services.msg.download import extract_attachment_file
from app.services.msg.raw_recovery import loose_candidates, raw_attachment_candidates


def _image(kind: str, size: tuple[int, int] = (24, 16)) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", size, (20, 120, 200)).save(buffer, kind)
    return buffer.getvalue()


def _jpeg_with_thumbnail() -> bytes:
    """JPEG cuyo segmento APP1 guarda otro JPEG completo, como una miniatura EXIF."""
    thumbnail = _image("JPEG", (8, 8))
    app1 = b"Exif\0\0" + thumbnail
    outer = _image("JPEG", (64, 48))
    return outer[:2] + b"\xff\xe1" + struct.pack(">H", len(app1) + 2) + app1 + outer[2:]


def _docx_with_stored_png() -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_STORED) as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("word/document.xml", "<document/>")
        archive.writestr("word/media/image1.png", _image("PNG"))
    return buffer.getvalue()


def _pdf(text: str) -> bytes:
    """PDF mínimo con ``startxref`` que apunta a su propia tabla."""
    body = f"%PDF-1.4\n1 0 obj\n<< /Texto ({text}) >>\nendobj\n".encode()
    return body + b"xref\n0 2\ntrailer\n<< >>\nstartxref\n" + str(len(body)).encode() + b"\n%%EOF\n"


def _loose(tmp_path, *parts: bytes):
    path = tmp_path / "sueltos.bin"
    path.write_bytes(b"relleno".join([b"inicio", *parts, b"fin"]))
    return [(item.name, item.content_type) for item in raw_attachment_candidates(path, set())]


def test_new_formats_are_validated_and_named_by_type(tmp_path):
    jpeg, gif, docx = _image("JPEG"), _image("GIF"), _docx_with_stored_png()

    assert _loose(tmp_path, jpeg, gif, docx) == [
        ("imagen-recuperado-1.jpg", "image/jpeg"),
        ("imagen-recuperado-2.gif", "image/gif"),
        (
            "documento-recuperado-1.docx",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ),
    ]


def test_truncated_files_are_rejected_but_intact_contents_survive(tmp_path):
    jpeg, gif, docx = _image("JPEG"), _image("GIF"), _docx_with_stored_png()

    # El DOCX cortado no cierra su directorio; la imagen que guardaba sin comprimir sí está entera.
    assert _loose(tmp_path, jpeg[: len(jpeg) // 2], gif[:-1], docx[:-30]) == [
        ("imagen-recuperado-1.png", "image/png")
    ]


def test_files_inside_other_files_are_not_separate_attachments(tmp_path):
    names = _loose(tmp_path, _jpeg_with_thumbnail(), _docx_with_stored_png())

    assert [name for name, _ in names] == ["imagen-recuperado-1.jpg", "documento-recuperado-1.docx"]


def test_each_pdf_ends_at_its_own_trailer(tmp_path):
    first, second = _pdf("primero"), _pdf("segundo")
    path = tmp_path / "pdfs.bin"
    path.write_bytes(b"x" * 10 + first + b"y" * 10 + second)

    sizes = [item.size for item in raw_attachment_candidates(path, set())]

    assert sizes == [len(first), len(second)]


def _msg_with_loose_jpeg(tmp_path, jpeg: bytes):
    """MSG legible con un DOCX adjunto y un JPEG en sectores que ningún stream reclama."""
    data = make_msg(attachment=_docx_with_stored_png(), filename="informe.docx")
    loose = jpeg.ljust(-(-len(jpeg) // SECTOR) * SECTOR, b"\0")
    path = tmp_path / "correo.msg"
    path.write_bytes(data + loose)
    return path


def test_streams_that_are_still_readable_are_never_loose(tmp_path):
    jpeg = _image("JPEG")
    path = _msg_with_loose_jpeg(tmp_path, jpeg)

    assert [(item.name, item.size) for item in loose_candidates(path)] == [
        ("imagen-recuperado-1.jpg", len(jpeg))
    ]


def test_loose_files_appear_only_when_the_parser_fails(tmp_path, monkeypatch):
    jpeg = _image("JPEG")
    path = _msg_with_loose_jpeg(tmp_path, jpeg)
    healthy = extract_msg_file(path, path.name, path.stat().st_size)
    assert [item.name for item in healthy.attachments] == ["informe.docx"]

    def fail(*args, **kwargs):
        raise RuntimeError("parser no disponible")

    monkeypatch.setattr(reader.extract_msg, "openMsg", fail)
    damaged = extract_msg_file(path, path.name, path.stat().st_size)
    assert [item.name for item in damaged.attachments] == [
        "informe.docx",
        "imagen-recuperado-1.jpg",
    ]
    output = tmp_path / "descarga.bin"
    assert extract_attachment_file(path, 1, output) == ("imagen-recuperado-1.jpg", "image/jpeg")
    assert output.read_bytes() == jpeg


def test_small_loose_file_inside_the_mini_stream_is_found(tmp_path):
    """Un adjunto pequeño sin entrada sigue en el mini stream: se rescata; el legible, no."""
    attached, lost = _image("PNG", (4, 4)), _image("PNG", (5, 5))
    path = tmp_path / "correo.msg"
    path.write_bytes(make_msg(attachment=attached, filename="icono.png"))
    with olefile.OleFileIO(str(path)) as container:
        sector_size, used = container.sectorsize, container.root.size
        sector, chain = container.root.isectStart, []
        while sector < len(container.fat):
            chain.append(sector)
            sector = container.fat[sector]
    slack = -(-used // 64) * 64
    assert slack + len(lost) <= len(chain) * sector_size
    offset = (chain[slack // sector_size] + 1) * sector_size + slack % sector_size
    data = bytearray(path.read_bytes())
    data[offset : offset + len(lost)] = lost
    path.write_bytes(data)

    assert [(item.name, item.size) for item in loose_candidates(path)] == [
        ("imagen-recuperado-1.png", len(lost))
    ]
