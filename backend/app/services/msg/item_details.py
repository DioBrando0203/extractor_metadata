"""Datos de una reunión, cita, contacto o tarea guardada como MSG (PEN-07).

extract_msg abre cada clase de mensaje con su propia clase (``MeetingRequest``, ``Contact``,
``Task``). Aquí se leen sólo los campos que una persona necesita ver. Son datos accesorios: uno
ilegible se omite sin advertencia y sin marcar el correo como parcial.
"""

from datetime import datetime

from app.models.schemas import ItemDetails, MetadataItem
from app.services.msg.text import clean_text

#: Prefijo de la clase de mensaje → tipo de elemento.
_KINDS = (
    ("ipm.schedule.meeting.request", "meeting"),
    ("ipm.schedule.meeting.canceled", "cancellation"),
    ("ipm.schedule.meeting.resp", "response"),
    ("ipm.appointment", "appointment"),
    ("ipm.contact", "contact"),
    ("ipm.task", "task"),
)
_GROUPS = {"contact": "Contacto", "task": "Tarea"}
_RESPONSES = {"pos": "Aceptada", "neg": "Rechazada", "tent": "Provisional"}
_TASK_STATUS = {
    "NOT_STARTED": "Sin iniciar",
    "IN_PROGRESS": "En curso",
    "COMPLETE": "Completada",
    "WAITING_ON_OTHER": "Esperando a otra persona",
    "DEFERRED": "Aplazada",
}
_MEETING_FIELDS = (
    ("Organizador", ("organizer",)),
    ("Obligatorios", ("toAttendeesString", "requiredAttendees")),
    ("Opcionales", ("ccAttendeesString", "optionalAttendees")),
    ("Repetición", ("recurrencePattern",)),
)
_CONTACT_FIELDS = (
    ("Nombre", ("displayName",)),
    ("Correo electrónico", ("email1EmailAddress",)),
    ("Otro correo", ("email2EmailAddress",)),
    ("Empresa", ("companyName",)),
    ("Cargo", ("jobTitle",)),
    ("Teléfono del trabajo", ("businessTelephoneNumber",)),
    ("Móvil", ("mobileTelephoneNumber",)),
    ("Teléfono de casa", ("homeTelephoneNumber",)),
    ("Dirección del trabajo", ("workAddress",)),
)


def item_kind(message_class: str | None) -> str | None:
    lowered = (message_class or "").lower()
    return next((kind for prefix, kind in _KINDS if lowered.startswith(prefix)), None)


def read_item(message: object) -> ItemDetails | None:
    """Datos del elemento según su clase de mensaje; ``None`` si es un correo."""
    message_class = _text(message, "classType")
    kind = item_kind(message_class)
    if kind is None:
        return None
    if kind == "contact":
        return _with_fields(ItemDetails(kind=kind), message, _CONTACT_FIELDS)
    if kind == "task":
        return _task(message)
    item = ItemDetails(
        kind=kind,
        start=_date(message, "appointmentStartWhole") or _date(message, "startDate"),
        end=_date(message, "appointmentEndWhole") or _date(message, "endDate"),
        all_day=bool(_value(message, "appointmentSubType")),
        location=_text(message, "location"),
    )
    _with_fields(item, message, _MEETING_FIELDS)
    if kind == "response":
        answer = _RESPONSES.get((message_class or "").rsplit(".", 1)[-1].lower())
        _add(item, "Respuesta", answer)
    return item


def _task(message: object) -> ItemDetails:
    item = ItemDetails(
        kind="task", start=_date(message, "taskStartDate"), end=_date(message, "taskDueDate")
    )
    status = _value(message, "taskStatus")
    _add(item, "Estado", _TASK_STATUS.get(getattr(status, "name", "")))
    percent = _value(message, "percentComplete")
    if isinstance(percent, (int, float)) and 0 <= percent <= 1:
        _add(item, "Completado", f"{percent * 100:.0f} %")
    _add(item, "Responsable", _text(message, "taskOwner"))
    return item


def _with_fields(
    item: ItemDetails, message: object, fields: tuple[tuple[str, tuple[str, ...]], ...]
) -> ItemDetails:
    for label, names in fields:
        _add(item, label, next((value for name in names if (value := _text(message, name))), None))
    return item


def _add(item: ItemDetails, label: str, value: str | None) -> None:
    if value:
        group = _GROUPS.get(item.kind, "Reunión")
        item.fields.append(MetadataItem(group=group, label=label, value=value))


def _value(message: object, name: str) -> object | None:
    try:
        return getattr(message, name, None)
    except Exception:
        # Propiedad accesoria ilegible: se omite (PY-16, resultado neutro).
        return None


def _text(message: object, name: str) -> str | None:
    value = _value(message, name)
    return clean_text(value) if isinstance(value, str) else None


def _date(message: object, name: str) -> datetime | None:
    value = _value(message, name)
    return value if isinstance(value, datetime) else None
