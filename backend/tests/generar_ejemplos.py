"""Genera MSG sintéticos para ver cada función en la interfaz (sin correos reales, QB-02).

Uso, desde ``backend/``:

    .venv/Scripts/python.exe tests/generar_ejemplos.py C:/ruta/de/salida   (Windows)
    .venv/bin/python tests/generar_ejemplos.py ~/msg_de_prueba              (Linux)

Reutiliza los mismos constructores que las pruebas; los archivos no se versionan (``*.msg`` está en
``.gitignore``).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from msg_factory import (  # noqa: E402
    attached_message,
    build_cfb,
    make_msg,
    message_streams,
    reference_attachment,
)
from test_archive import _mail  # noqa: E402
from test_eml import _eml, _with_file  # noqa: E402
from test_item_details import _meeting  # noqa: E402
from test_rescue import _damaged  # noqa: E402
from test_smime import ENVELOPED_DATA, _clear_signed, _smime_msg  # noqa: E402

FOLDER = "__attach_version1.0_#{:08X}"
LINKED_MAIL_BODY = (
    "Revisa el informe final <https://contoso.example.test/informe?id=7>.\r\n\r\n"
    "También está el portal de la obra: https://obra.example.test/planos"
)


def _forwarded_with_link() -> bytes:
    inner = message_streams(
        subject="Cotización interna",
        sender="proveedor@example.test",
        body="Texto del correo reenviado.",
        attachment=b"%PDF-1.4 cotizacion %%EOF",
        filename="informe.pdf",
    )
    streams = attached_message(FOLDER.format(0), inner, "Cotización interna")
    streams.update(
        reference_attachment(
            FOLDER.format(1),
            "Presupuesto.xlsx",
            "https://contoso.sharepoint.example.test/sites/obra/Presupuesto.xlsx",
        )
    )
    body = "Te reenvío el correo del proveedor. El presupuesto está en SharePoint."
    subject = "Reenvío con correo adjunto y archivo en la nube"
    return build_cfb(message_streams(subject=subject, body=body, extra_streams=streams))


def examples() -> dict[str, bytes]:
    """Nombre de archivo → bytes de cada ejemplo, en el orden de la guía del README."""
    return {
        "1 - Correo adjunto y enlace a la nube.msg": _forwarded_with_link(),
        "2 - Reunion.msg": _meeting(),
        "3 - Firmado digitalmente.msg": _smime_msg(
            "IPM.Note.SMIME.MultipartSigned", _clear_signed()
        ),
        "4 - Cifrado.msg": _smime_msg("IPM.Note.SMIME", ENVELOPED_DATA),
        "5 - Varios adjuntos (Descargar todo).msg": _mail(),
        "6 - EML adjunto.msg": _with_file("cotizacion.eml", _eml()),
        "7 - Cabecera danada (rescate).msg": _damaged(header_bytes=512)[0],
        "8 - Enlaces en el texto.msg": make_msg(
            subject="Enlaces en el cuerpo", body=LINKED_MAIL_BODY
        ),
    }


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 1
    output = Path(sys.argv[1])
    output.mkdir(parents=True, exist_ok=True)
    for name, data in examples().items():
        (output / name).write_bytes(data)
        print(f"{len(data):>8} bytes  {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
