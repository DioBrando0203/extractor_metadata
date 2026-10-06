"""Vistas previas con archivos sintéticos: imágenes, DWG, DXF y Office generados en la prueba."""

from __future__ import annotations

import base64
import io
import zipfile
from dataclasses import replace

import pytest
from fastapi.testclient import TestClient
from msg_factory import make_msg
from PIL import Image

from app.api.routes import messages
from app.main import app
from app.services import metadata, previews
from app.services.msg import extract_msg_file
from app.services.previews import embedded


def _image(fmt: str, size: tuple[int, int] = (64, 40), mode: str = "RGB") -> bytes:
    output = io.BytesIO()
    Image.new(mode, size, (200, 30, 30) if mode == "RGB" else None).save(output, fmt)
    return output.getvalue()


def _dib(size: tuple[int, int] = (24, 16)) -> bytes:
    """BMP sin su cabecera de archivo: así guardan AutoCAD y DXF sus miniaturas."""
    return _image("BMP", size)[14:]


def _dwg_with_preview(code: int, data: bytes) -> bytes:
    """DWG mínimo: firma, dirección de la imagen en 0x0D y sección con centinela y registros."""
    address = 0x80
    records_start = address + 16 + 5
    data_start = records_start + 9
    header = bytearray(b"AC1032" + b"\0" * (address - 6))
    header[0x0D:0x11] = address.to_bytes(4, "little")
    section = (
        embedded.DWG_IMAGE_SENTINEL
        + (9 + len(data)).to_bytes(4, "little")
        + bytes([1])
        + bytes([code])
        + data_start.to_bytes(4, "little")
        + len(data).to_bytes(4, "little")
    )
    return bytes(header) + section + data


def _decode(data_uri: str) -> Image.Image:
    assert data_uri.startswith("data:image/jpeg;base64,")
    return Image.open(io.BytesIO(base64.b64decode(data_uri.split(",", 1)[1])))


def test_image_thumbnail_keeps_ratio_and_fits_bounds():
    uri, source = previews.thumbnail_data_uri(_image("PNG", (1200, 600)), "foto.png")
    assert source == "image"
    image = _decode(uri)
    assert image.format == "JPEG"
    assert image.size == (previews.THUMBNAIL_SIZE, previews.THUMBNAIL_SIZE // 2)


def test_transparent_image_is_flattened_on_white():
    rgba = io.BytesIO()
    Image.new("RGBA", (10, 10), (0, 0, 0, 0)).save(rgba, "PNG")
    uri, _ = previews.thumbnail_data_uri(rgba.getvalue(), "logo.png")
    assert _decode(uri).convert("RGB").getpixel((5, 5)) == (255, 255, 255)


@pytest.mark.parametrize("fmt", ["JPEG", "GIF", "BMP", "TIFF", "WEBP"])
def test_common_image_formats_have_preview(fmt):
    uri, source = previews.thumbnail_data_uri(_image(fmt), f"imagen.{fmt.lower()}")
    assert uri and source == "image"


def test_dwg_png_preview_saved_by_autocad():
    uri, source = previews.thumbnail_data_uri(_dwg_with_preview(6, _image("PNG")), "plano.dwg")
    assert source == "embedded"
    assert _decode(uri).size == (64, 40)


def test_dwg_bmp_preview_saved_by_autocad():
    uri, source = previews.thumbnail_data_uri(_dwg_with_preview(2, _dib()), "plano.dwg")
    assert source == "embedded"
    assert _decode(uri).size == (24, 16)


def test_dwg_without_preview_or_with_broken_section_is_ignored():
    assert previews.thumbnail_data_uri(b"AC1032" + b"0" * 64, "plano.dwg") == (None, None)
    broken = bytearray(_dwg_with_preview(6, _image("PNG")))
    broken[0x80] ^= 0xFF  # centinela alterado
    assert previews.thumbnail_data_uri(bytes(broken), "plano.dwg") == (None, None)


def test_dxf_thumbnailimage_section():
    hex_lines = "\n".join(f"310\n{chunk}" for chunk in _chunks(_dib().hex().upper(), 254))
    dxf = (
        "0\nSECTION\n2\nHEADER\n0\nENDSEC\n"
        f"0\nSECTION\n2\nTHUMBNAILIMAGE\n90\n{len(_dib())}\n{hex_lines}\n0\nENDSEC\n0\nEOF\n"
    ).encode("latin-1")
    uri, source = previews.thumbnail_data_uri(dxf, "plano.dxf")
    assert source == "embedded"
    assert _decode(uri).size == (24, 16)


def test_office_docprops_thumbnail():
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("ppt/presentation.xml", "<presentation/>")
        archive.writestr("docProps/thumbnail.jpeg", _image("JPEG", (80, 60)))
    uri, source = previews.thumbnail_data_uri(output.getvalue(), "avance.pptx")
    assert source == "embedded"
    assert _decode(uri).size == (80, 60)


def test_unsupported_or_dangerous_formats_are_not_decoded():
    eps = b"%!PS-Adobe-3.0 EPSF-3.0\n%%BoundingBox: 0 0 10 10\nshowpage\n"
    assert previews.thumbnail_data_uri(eps, "figura.eps") == (None, None)
    assert previews.thumbnail_data_uri(eps, "figura.png") == (None, None)
    assert previews.thumbnail_data_uri(b"%PDF-1.7\n", "informe.pdf") == (None, None)
    assert previews.thumbnail_data_uri(b"", "vacio.png") == (None, None)


def test_dwg_metadata_reports_embedded_thumbnail():
    _, items, _ = metadata.extract_file_metadata(_dwg_with_preview(6, _image("PNG")), "plano.dwg")
    values = {item.label: item.value for item in items}
    assert values["Miniatura incrustada"] == "Sí"


def test_extraction_response_includes_attachment_preview(tmp_path):
    path = tmp_path / "correo.msg"
    path.write_bytes(make_msg(attachment=_image("PNG"), filename="foto.png"))
    attachment = extract_msg_file(path, "correo.msg", path.stat().st_size).attachments[0]
    assert attachment.preview_source == "image"
    assert _decode(attachment.preview).size == (64, 40)


def test_preview_budget_drops_extra_thumbnails_without_partial(tmp_path, monkeypatch):
    from app.services.msg import limits

    path = tmp_path / "correo.msg"
    path.write_bytes(make_msg(attachment=_image("PNG"), filename="foto.png"))
    baseline = extract_msg_file(path, "correo.msg", path.stat().st_size)
    monkeypatch.setattr(
        limits,
        "settings",
        replace(limits.settings, max_total_preview_chars=10),
    )
    message = extract_msg_file(path, "correo.msg", path.stat().st_size)
    assert baseline.attachments[0].preview is not None
    assert message.attachments[0].preview is None
    assert message.status == baseline.status
    assert message.warnings == baseline.warnings


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(messages, "settings", replace(messages.settings, temp_root=tmp_path))
    with TestClient(app, base_url="http://localhost") as local_client:
        yield local_client
    assert list(tmp_path.iterdir()) == []


def test_large_preview_endpoint_converts_tiff_to_jpeg(client):
    response = client.post(
        "/api/messages/attachment",
        data={"attachment_index": "0", "preview": "true"},
        files={"file": ("correo.msg", make_msg(attachment=_image("TIFF"), filename="scan.tif"))},
    )
    assert response.status_code == 200, response.text
    assert response.headers["content-type"] == "image/jpeg"
    assert Image.open(io.BytesIO(response.content)).format == "JPEG"


def test_large_preview_endpoint_rejects_files_without_preview(client):
    response = client.post(
        "/api/messages/attachment",
        data={"attachment_index": "0", "preview": "true"},
        files={"file": ("correo.msg", make_msg(attachment=b"AC1032" + b"0" * 64))},
    )
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "NO_PREVIEW"


def _chunks(text: str, size: int) -> list[str]:
    return [text[index : index + size] for index in range(0, len(text), size)]
