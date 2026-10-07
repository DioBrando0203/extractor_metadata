"""Lectura de archivos MSG. API pública: ``extract_msg_file``, ``extract_attachment_file`` y
``extract_all_attachments``.

Módulos: ``reader`` orquesta; ``ole_reader`` lee el contenedor; ``attachment_entries`` describe
cómo viaja cada adjunto; ``attachments`` arma adjuntos; ``embedded`` abre correos adjuntos;
``raw_recovery`` rescata archivos sueltos (``raw_formats``, ``raw_images``, ``sector_map``);
``fat_recovery`` repone la firma y la DIFAT en una copia; ``rescue`` lee sin cabecera;
``download`` materializa un adjunto; ``limits`` acota la respuesta; ``names`` y ``text`` son
utilidades puras.
"""

from app.services.msg.archive import extract_all_attachments
from app.services.msg.download import extract_attachment_file
from app.services.msg.reader import extract_msg_file

__all__ = ["extract_all_attachments", "extract_attachment_file", "extract_msg_file"]
