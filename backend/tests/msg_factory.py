"""MSG sintéticos CFB v4: fixtures propios sin correos ni archivos privados."""

import math
import struct
import uuid

FREE = 0xFFFFFFFF
END = 0xFFFFFFFE
FAT = 0xFFFFFFFD
SECTOR = 4096


def build_cfb(streams: dict[tuple[str, ...], bytes]) -> bytes:
    paths = {()}
    for path in streams:
        for depth in range(1, len(path) + 1):
            paths.add(path[:depth])
    entries = sorted(paths, key=lambda value: (len(value), value))
    indices = {path: index for index, path in enumerate(entries)}
    sectors: list[bytes] = []
    fat: list[int] = []

    def allocate(payload: bytes) -> tuple[int, int]:
        if not payload:
            return END, 0
        start = len(sectors)
        count = math.ceil(len(payload) / SECTOR)
        for index in range(count):
            sectors.append(payload[index * SECTOR : (index + 1) * SECTOR].ljust(SECTOR, b"\0"))
            fat.append(start + index + 1 if index + 1 < count else END)
        return start, count

    mini_data = bytearray()
    mini_fat: list[int] = []
    starts: dict[tuple[str, ...], int] = {}
    for path, payload in streams.items():
        if len(payload) >= 4096:
            starts[path], _ = allocate(payload)
        elif payload:
            start = len(mini_fat)
            count = math.ceil(len(payload) / 64)
            starts[path] = start
            mini_data.extend(payload.ljust(count * 64, b"\0"))
            mini_fat.extend(
                start + index + 1 if index + 1 < count else END for index in range(count)
            )
        else:
            starts[path] = END
    root_start, _ = allocate(bytes(mini_data))
    minifat_bytes = b"".join(struct.pack("<I", value) for value in mini_fat)
    if minifat_bytes:
        minifat_bytes = minifat_bytes.ljust(
            math.ceil(len(minifat_bytes) / SECTOR) * SECTOR, b"\xff"
        )
    minifat_start, minifat_count = allocate(minifat_bytes)
    left = [FREE] * len(entries)
    right = [FREE] * len(entries)
    child = [FREE] * len(entries)

    def tree(nodes: list[int]) -> int:
        if not nodes:
            return FREE
        midpoint = len(nodes) // 2
        node = nodes[midpoint]
        left[node] = tree(nodes[:midpoint])
        right[node] = tree(nodes[midpoint + 1 :])
        return node

    for index, path in enumerate(entries):
        children = [indices[other] for other in entries if other and other[:-1] == path]
        children.sort(key=lambda node: (len(entries[node][-1]), entries[node][-1].upper()))
        child[index] = tree(children)
    directory = bytearray()
    for index, path in enumerate(entries):
        name = path[-1] if path else "Root Entry"
        encoded_name = (name + "\0").encode("utf-16-le")
        entry = bytearray(128)
        entry[: len(encoded_name)] = encoded_name
        struct.pack_into("<H", entry, 64, len(encoded_name))
        entry[66] = 5 if not path else 2 if path in streams else 1
        entry[67] = 1
        struct.pack_into("<III", entry, 68, left[index], right[index], child[index])
        start = root_start if not path else starts.get(path, END)
        size = len(mini_data) if not path else len(streams.get(path, b""))
        struct.pack_into("<IQ", entry, 116, start, size)
        directory.extend(entry)
    directory_start, directory_count = allocate(bytes(directory))
    fat_count = math.ceil((len(sectors) + 1) / (SECTOR // 4))
    while math.ceil((len(sectors) + fat_count) / (SECTOR // 4)) > fat_count:
        fat_count += 1
    assert fat_count <= 109, "Fixture demasiado grande para DIFAT de cabecera"
    fat_ids = list(range(len(sectors), len(sectors) + fat_count))
    fat.extend([FAT] * fat_count)
    fat_values = fat + [FREE] * (fat_count * SECTOR // 4 - len(fat))
    fat_payload = struct.pack(f"<{len(fat_values)}I", *fat_values)
    sectors.extend(fat_payload[index * SECTOR : (index + 1) * SECTOR] for index in range(fat_count))
    header = bytearray(SECTOR)
    header[:8] = bytes.fromhex("D0CF11E0A1B11AE1")
    struct.pack_into("<HHHHH", header, 24, 0x003E, 4, 0xFFFE, 12, 6)
    struct.pack_into(
        "<IIIIIIIII",
        header,
        40,
        directory_count,
        fat_count,
        directory_start,
        0,
        4096,
        minifat_start,
        minifat_count,
        END,
        0,
    )
    struct.pack_into("<109I", header, 76, *(fat_ids + [FREE] * (109 - len(fat_ids))))
    return bytes(header) + b"".join(sectors)


def make_msg(**options: object) -> bytes:
    """MSG mínimo. ``omit`` quita propiedades (p. ej. ``("0037",)``) para simular daños."""
    return build_cfb(message_streams(**options))


def message_streams(
    *,
    subject: str = "Mensaje de prueba — áéíóú",
    sender: str = "equipo@example.test",
    body: str = "Contenido de prueba local.",
    attachment: bytes | None = None,
    filename: str = "plano.dwg",
    extra_streams: dict[tuple[str, ...], bytes] | None = None,
    omit: tuple[str, ...] = (),
    headers: str | None = None,
    html: str | None = None,
    content_id: str | None = None,
    message_class: str = "IPM.Note",
    properties: dict[str, str] | None = None,
    named: tuple[tuple[str, int, str, bytes], ...] = (),
) -> dict[tuple[str, ...], bytes]:
    """Streams de un MSG mínimo, para construirlo o adjuntarlo dentro de otro.

    ``properties`` agrega textos MAPI por identificador (``{"3A16": "Empresa"}``) y ``named``,
    propiedades con nombre ``(GUID, LID, tipo, valor)`` como las de reuniones y tareas.
    """
    strings = {
        "001A": message_class,
        "0037": subject,
        "0C1A": "Equipo local",
        "0C1F": sender,
        "0E04": "lector@example.test",
        "1000": body,
        "007D": f"From: {sender}\r\nTo: lector@example.test\r\n"
        "Date: Mon, 05 Oct 2026 10:00:00 -0500\r\n"
        "Message-ID: <local@example.test>\r\n",
    }
    if headers is not None:
        strings["007D"] = headers
    strings.update(properties or {})
    streams = {
        (f"__substg1.0_{key}001F",): value.encode("utf-16-le")
        for key, value in strings.items()
        if key not in omit
    }
    if html is not None:
        streams[("__substg1.0_10130102",)] = html.encode("utf-8")
    named_streams, fixed = named_properties(named)
    streams.update(named_streams)
    flags = struct.pack("<II8s", 0x340D0003, 6, struct.pack("<I", 0x40000) + b"\0" * 4)
    streams[("__properties_version1.0",)] = (
        struct.pack("<8xIIII8x", 0, 1 if attachment else 0, 0, 1 if attachment else 0)
        + flags
        + b"".join(fixed)
    )
    if attachment is not None:
        folder = "__attach_version1.0_#00000000"
        streams[(folder, "__properties_version1.0")] = attachment_properties(1)
        streams[(folder, "__substg1.0_3707001F")] = filename.encode("utf-16-le")
        streams[(folder, "__substg1.0_37010102")] = attachment
        if content_id is not None:
            streams[(folder, "__substg1.0_3712001F")] = content_id.encode("utf-16-le")
    streams.update(extra_streams or {})
    return streams


def named_properties(
    named: tuple[tuple[str, int, str, bytes], ...],
) -> tuple[dict[tuple[str, ...], bytes], list[bytes]]:
    """Tabla ``__nameid_version1.0`` y valores de propiedades con nombre numéricas.

    Cada propiedad ``n`` se guarda como ``0x8000 + n``: los textos y binarios en su stream y los
    valores de tamaño fijo (fecha, booleano, entero) como entradas del stream de propiedades.
    """
    guids: list[str] = []
    entries = b""
    streams: dict[tuple[str, ...], bytes] = {}
    fixed: list[bytes] = []
    for index, (guid, lid, prop_type, value) in enumerate(named):
        if guid not in guids:
            guids.append(guid)
        entries += struct.pack("<IHH", lid, (guids.index(guid) + 3) << 1, index)
        prop_id = 0x8000 + index
        if prop_type in ("001F", "0102"):
            streams[(f"__substg1.0_{prop_id:04X}{prop_type}",)] = value
        else:
            tag = (prop_id << 16) | int(prop_type, 16)
            fixed.append(struct.pack("<II8s", tag, 6, value.ljust(8, b"\0")))
    folder = "__nameid_version1.0"
    streams[(folder, "__substg1.0_00020102")] = b"".join(uuid.UUID(g).bytes_le for g in guids)
    streams[(folder, "__substg1.0_00030102")] = entries
    streams[(folder, "__substg1.0_00040102")] = b""
    return streams, fixed


def attachment_properties(method: int) -> bytes:
    """Stream de propiedades de un adjunto con su ``PidTagAttachMethod``."""
    entry = struct.pack("<II8s", 0x37050003, 6, struct.pack("<I", method) + b"\0" * 4)
    return b"\0" * 8 + entry


def attached_message(
    folder: str, inner: dict[tuple[str, ...], bytes], display_name: str | None = None
) -> dict[tuple[str, ...], bytes]:
    """Coloca un correo (``message_streams``) como correo adjunto (método 5) en ``folder``.

    Como en Outlook, el correo interno usa las propiedades con nombre del contenedor y su stream
    de propiedades raíz tiene 24 bytes de encabezado en lugar de 32.
    """
    streams = {(folder, "__properties_version1.0"): attachment_properties(5)}
    if display_name is not None:
        streams[(folder, "__substg1.0_3001001F")] = display_name.encode("utf-16-le")
    for path, payload in inner.items():
        if path[0] == "__nameid_version1.0":
            continue
        if path == ("__properties_version1.0",):
            payload = payload[:24] + payload[32:]
        streams[(folder, "__substg1.0_3701000D", *path)] = payload
    return streams


def reference_attachment(
    folder: str, name: str, address: str | None, method: int = 7
) -> dict[tuple[str, ...], bytes]:
    """Adjunto por referencia: sólo nombre y dirección (OneDrive, SharePoint o una ruta)."""
    streams = {
        (folder, "__properties_version1.0"): attachment_properties(method),
        (folder, "__substg1.0_3707001F"): name.encode("utf-16-le"),
    }
    if address is not None:
        streams[(folder, "__substg1.0_370D001F")] = address.encode("utf-16-le")
    return streams
