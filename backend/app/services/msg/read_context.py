"""Datos que comparten las dos estrategias de lectura de ``reader`` (Parameter Object).

Reúne el contenedor ya abierto, las advertencias, el presupuesto de correos adjuntos y lo que decide
qué adjuntos se muestran: los del árbol OLE, los sueltos rescatados o, en un correo firmado en
claro, los del contenido firmado (``smime``).
"""

from dataclasses import dataclass
from pathlib import Path

from app.models.schemas import AttachmentMetadata
from app.services.msg.attachments import AttachmentSources
from app.services.msg.embedded import AttachedMessages, ReadMessage
from app.services.msg.eml import body_text, read_parts
from app.services.msg.envelope import Envelope, envelope_from_headers, envelope_from_properties
from app.services.msg.nesting import EmbeddedBudget
from app.services.msg.ole_reader import OleMetadata
from app.services.msg.raw_recovery import raw_recovered_attachments
from app.services.msg.smime import SmimeContent

_ATTACHMENT_NOTICE = "Uno o más adjuntos tienen advertencias; consulta la pestaña Adjuntos."


@dataclass
class ReadContext:
    """Datos comunes a las dos estrategias de lectura."""

    path: Path
    original_name: str
    size_bytes: int
    ole: OleMetadata
    warnings: list[str]
    #: Se reparó la cabecera o la FAT en una copia: puede haber archivos sueltos.
    structure_repaired: bool
    budget: EmbeddedBudget
    #: Lee un MSG con este mismo flujo; lo aporta ``reader`` para abrir correos adjuntos.
    read: ReadMessage
    #: Correo S/MIME: firmado (con su contenido si es en claro) o cifrado.
    smime: SmimeContent | None = None
    #: El parser MSG no abrió el archivo: también puede haber archivos sueltos.
    parser_failed: bool = False

    @property
    def deadline(self) -> float:
        return self.budget.deadline

    def sources(self) -> AttachmentSources:
        """Datos de adjuntos y cómo abrir un correo adjunto con este mismo flujo."""
        messages = AttachedMessages(self.path, self.budget, self.read)
        return AttachmentSources(self.ole.attachments, self.deadline, messages)

    def fallback_envelope(self) -> list[Envelope]:
        """Respaldos en orden de confianza: propiedades MAPI y luego encabezados de transporte."""
        recovered = self.ole.recovered
        return [envelope_from_properties(recovered), envelope_from_headers(recovered.get("007D"))]

    def finish_attachments(self, attachments: list[AttachmentMetadata]) -> list[AttachmentMetadata]:
        """Adjuntos que se muestran y aviso si alguno tiene advertencias.

        Firmado en claro: los del contenido firmado en lugar del ``smime.p7m``. Con daño: se suman
        los archivos sueltos rescatados.
        """
        if self.smime and self.smime.content is not None:
            attachments = read_parts(self.smime.content, self.budget)
        elif self.structure_repaired or self.parser_failed:
            attachments.extend(raw_recovered_attachments(self.path, self.deadline))
        if any(item.warnings for item in attachments):
            self.warnings.append(_ATTACHMENT_NOTICE)
        return attachments

    def signed_body(self, body: str | None) -> str | None:
        """Cuerpo de un correo S/MIME: en claro, el leído o el del contenido firmado.

        Opaco o cifrado: extract_msg desenvuelve el ``.p7m`` como si fuera texto y daría bytes sin
        sentido; sólo vale el texto guardado aparte (``1000``), si lo hay.
        """
        if not self.smime:
            return body
        if self.smime.content is None:
            return self.ole.recovered.get("1000")
        return body or body_text(self.smime.content)

    @property
    def security(self) -> str | None:
        return self.smime.security if self.smime else None
