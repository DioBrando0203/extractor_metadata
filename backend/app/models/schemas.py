from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class MetadataItem(BaseModel):
    group: str
    label: str
    value: str


class AttachmentMetadata(BaseModel):
    name: str
    content_type: str | None = None
    size_bytes: int | None = None
    metadata: list[MetadataItem] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    # Miniatura JPEG como data URI. ``embedded``: la guardó el propio archivo (DWG, DXF, Office).
    preview: str | None = None
    preview_source: Literal["image", "embedded"] | None = None
    # Content-ID sin "<>": el cuerpo lo referencia como "[cid:…]" donde va la imagen incrustada.
    content_id: str | None = None
    # True si el archivo perdió el Content-ID y se reconstruyó por las medidas de la imagen.
    content_id_inferred: bool = False
    # Cómo viaja: "file" trae sus bytes; "message" es un correo adjunto, leído en ``message``;
    # "link" vive en una ruta o en la nube y el correo sólo guarda su dirección en ``link``.
    kind: Literal["file", "message", "link"] = "file"
    link: str | None = None
    message: "MessageMetadata | None" = None


class ItemDetails(BaseModel):
    """Datos propios de un MSG que no es un correo: reunión, cita, contacto o tarea."""

    kind: Literal["meeting", "cancellation", "response", "appointment", "contact", "task"]
    # Reunión o cita: cuándo empieza y termina. Tarea: inicio y vencimiento.
    start: datetime | None = None
    end: datetime | None = None
    all_day: bool = False
    location: str | None = None
    # Resto de datos en el orden en que se muestran: organizador, asistentes, teléfonos, estado…
    fields: list[MetadataItem] = Field(default_factory=list)


class MessageMetadata(BaseModel):
    file_name: str
    file_size_bytes: int
    subject: str | None = None
    sender: str | None = None
    recipients: list[str] = Field(default_factory=list)
    sent_at: datetime | None = None
    received_at: datetime | None = None
    body_preview: str | None = None
    body_truncated: bool = False
    status: Literal["complete", "partial"] = "complete"
    headers: list[MetadataItem] = Field(default_factory=list)
    properties: list[MetadataItem] = Field(default_factory=list)
    attachments: list[AttachmentMetadata] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    # Reunión, cita, contacto o tarea; ``None`` en un correo.
    item: ItemDetails | None = None
    # Correo S/MIME: ``signed`` (firmado en claro; la firma no se verifica), ``opaque`` (firmado
    # dentro del .p7m, no se desempaqueta), ``encrypted`` (sin la clave no se lee) o ``protected``
    # (permisos IRM: sólo Outlook con una cuenta autorizada).
    security: Literal["signed", "opaque", "encrypted", "protected"] | None = None


AttachmentMetadata.model_rebuild()


class ExtractionResponse(BaseModel):
    message: MessageMetadata
    processed_locally: bool = True
