import struct

from msg_factory import build_cfb

from app.services.message_extractor import extract_msg_file


def test_ansi_codepage_is_respected_in_parser_and_raw_metadata(tmp_path):
    flags = struct.pack("<II8s", 0x340D0003, 6, b"\0" * 8)
    codepage = struct.pack("<II8s", 0x3FFD0003, 6, struct.pack("<I", 932) + b"\0" * 4)
    streams = {
        ("__properties_version1.0",): b"\0" * 32 + flags + codepage,
        ("__substg1.0_001A001E",): b"IPM.Note",
        ("__substg1.0_0037001E",): "日本語".encode("cp932"),
        ("__substg1.0_1000001E",): "本文".encode("cp932"),
    }
    for tag in ("00020102", "00030102", "00040102"):
        streams[("__nameid_version1.0", f"__substg1.0_{tag}")] = b""
    path = tmp_path / "ansi.msg"
    path.write_bytes(build_cfb(streams))
    result = extract_msg_file(path, path.name, path.stat().st_size)
    assert result.subject == "日本語"
    assert result.body_preview == "本文"
    assert "日本語" in {item.value for item in result.properties}
