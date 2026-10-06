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


class ExtractionResponse(BaseModel):
    message: MessageMetadata
    processed_locally: bool = True
