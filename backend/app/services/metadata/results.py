"""Tipos compartidos por los extractores de metadatos y utilidades para acotar sus valores."""

import json
from dataclasses import dataclass, field

from app.core.config import settings
from app.models.schemas import MetadataItem


@dataclass(frozen=True)
class DetectedFile:
    kind: str
    content_type: str | None
    extension: str
    signature: str


@dataclass
class ExtractionResult:
    items: list[MetadataItem] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def stringify(value: object) -> tuple[str, bool]:
    """Da una representación pequeña, serializable y sin binarios en la respuesta."""
    if isinstance(value, bytes):
        text = f"<binario: {len(value):,} bytes>"
    elif isinstance(value, (dict, list, tuple)):
        try:
            text = json.dumps(value, ensure_ascii=False, default=str)
        except (TypeError, ValueError):
            text = str(value)
    else:
        text = str(value)
    if len(text) <= settings.max_property_chars:
        return text, False
    return (
        f"{text[: settings.max_property_chars]} … [truncado; {len(text):,} caracteres en origen]",
        True,
    )


def add_item(result: ExtractionResult, group: str, label: str, value: object) -> None:
    safe_group, group_cut = stringify(group)
    safe_label, label_cut = stringify(label)
    safe_value, value_cut = stringify(value)
    if len(safe_label) > 256:
        safe_label = f"{safe_label[:256]} …"
        label_cut = True
    result.items.append(MetadataItem(group=safe_group, label=safe_label, value=safe_value))
    if group_cut or label_cut or value_cut:
        result.warnings.append(
            "Se truncó un valor de metadatos demasiado grande para la respuesta."
        )


def limited(result: ExtractionResult, source: str) -> ExtractionResult:
    if len(result.items) > settings.max_properties:
        omitted = len(result.items) - settings.max_properties
        result.items = result.items[: settings.max_properties]
        result.warnings.append(
            f"{source}: se omitieron {omitted:,} metadatos para mantener una respuesta legible."
        )
    result.warnings = list(dict.fromkeys(result.warnings))
    return result
