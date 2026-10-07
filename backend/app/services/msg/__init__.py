"""Lectura de archivos MSG. API pública: ``extract_msg_file`` y ``extract_attachment_file``.

Módulos: ``reader`` orquesta; ``ole_reader`` lee el contenedor; ``attachment_entries`` describe
cómo viaja cada adjunto; ``attachments`` arma adjuntos; ``embedded`` abre correos adjuntos;
``raw_recovery`` rescata PNG/PDF sueltos; ``fat_recovery`` repara una copia de la DIFAT;
``download`` materializa un adjunto; ``limits`` acota la respuesta; ``names`` y ``text`` son
utilidades puras.
"""

from app.services.msg.download import extract_attachment_file
from app.services.msg.reader import extract_msg_file

__all__ = ["extract_attachment_file", "extract_msg_file"]
