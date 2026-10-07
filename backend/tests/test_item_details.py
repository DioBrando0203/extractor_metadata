"""Reuniones, citas, contactos y tareas guardados como MSG (PEN-07)."""

import struct
from datetime import UTC, datetime

from msg_factory import make_msg

from app.services.msg import extract_msg_file
from app.services.msg.item_details import item_kind

APPOINTMENT = "{00062002-0000-0000-C000-000000000046}"
ADDRESS = "{00062004-0000-0000-C000-000000000046}"
TASK = "{00062003-0000-0000-C000-000000000046}"
START = datetime(2026, 10, 12, 15, 0, tzinfo=UTC)
END = datetime(2026, 10, 12, 16, 30, tzinfo=UTC)


def _filetime(value: datetime) -> bytes:
    epoch = datetime(1601, 1, 1, tzinfo=UTC)
    return struct.pack("<Q", int((value - epoch).total_seconds() * 10_000_000))


def _text(value: str) -> bytes:
    return value.encode("utf-16-le")


def _meeting(message_class: str = "IPM.Schedule.Meeting.Request") -> bytes:
    return make_msg(
        subject="Revisión de planos",
        message_class=message_class,
        properties={"0042": "María Fernández"},
        named=(
            (APPOINTMENT, 0x820D, "0040", _filetime(START)),
            (APPOINTMENT, 0x820E, "0040", _filetime(END)),
            (APPOINTMENT, 0x8208, "001F", _text("Sala 3, piso 2")),
            (APPOINTMENT, 0x823B, "001F", _text("Ana Pérez; Luis Rojas")),
            (APPOINTMENT, 0x823C, "001F", _text("Carlos Medina")),
            (APPOINTMENT, 0x8232, "001F", _text("Cada semana el lunes")),
        ),
    )


def _extract(tmp_path, data: bytes):
    path = tmp_path / "elemento.msg"
    path.write_bytes(data)
    return extract_msg_file(path, path.name, len(data))


def test_meeting_request_shows_when_where_and_who(tmp_path):
    result = _extract(tmp_path, _meeting())

    item = result.item
    assert item.kind == "meeting"
    assert (item.start, item.end, item.all_day) == (START, END, False)
    assert item.location == "Sala 3, piso 2"
    assert [(field.label, field.value) for field in item.fields] == [
        ("Organizador", "María Fernández"),
        ("Obligatorios", "Ana Pérez; Luis Rojas"),
        ("Opcionales", "Carlos Medina"),
        ("Repetición", "Cada semana el lunes"),
    ]
    assert result.status == "complete"


def test_meeting_response_says_the_answer(tmp_path):
    item = _extract(tmp_path, _meeting("IPM.Schedule.Meeting.Resp.Tent")).item

    assert item.kind == "response"
    assert ("Respuesta", "Provisional") in [(field.label, field.value) for field in item.fields]


def test_contact_card_and_task_status(tmp_path):
    contact = make_msg(
        subject="Ana Pérez",
        message_class="IPM.Contact",
        properties={"3001": "Ana Pérez", "3A16": "Constructora Andina", "3A1C": "+51 999 111 222"},
        named=((ADDRESS, 0x8083, "001F", _text("ana@example.test")),),
    )
    task = make_msg(
        subject="Enviar metrados",
        message_class="IPM.Task",
        named=(
            (TASK, 0x8105, "0040", _filetime(END)),
            (TASK, 0x8101, "0003", struct.pack("<I", 1)),
            (TASK, 0x8102, "0005", struct.pack("<d", 0.5)),
        ),
    )

    card = _extract(tmp_path, contact).item
    todo = _extract(tmp_path, task).item

    assert card.kind == "contact"
    assert [(field.label, field.value) for field in card.fields] == [
        ("Nombre", "Ana Pérez"),
        ("Correo electrónico", "ana@example.test"),
        ("Empresa", "Constructora Andina"),
        ("Móvil", "+51 999 111 222"),
    ]
    assert (todo.kind, todo.end) == ("task", END)
    assert [(field.label, field.value) for field in todo.fields] == [
        ("Estado", "En curso"),
        ("Completado", "50 %"),
    ]


def test_ordinary_mail_has_no_item(tmp_path):
    assert _extract(tmp_path, make_msg()).item is None
    assert item_kind("IPM.Note") is None
    assert item_kind("IPM.Schedule.Meeting.Canceled") == "cancellation"
    assert item_kind("IPM.Appointment") == "appointment"
