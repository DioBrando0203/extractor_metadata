"""Convierte un cuerpo HTML a texto sin ejecutar contenido ni resolver recursos.

Las imágenes incrustadas (``<img src="cid:…">``) se conservan como marcadores ``[cid:…]`` en su
posición, la misma convención que Outlook usa en el cuerpo de texto plano. Imágenes remotas y
cualquier otro recurso externo se descartan. Cada enlace ``http``/``https`` conserva su destino real
como ``texto <url>`` (como el texto plano de Outlook), salvo que el texto ya sea la dirección: así
un "haz clic aquí" deja ver adónde lleva.
"""

from html.parser import HTMLParser

_HIDDEN = {"script", "style", "head"}
_BLOCKS = {"br", "p", "div", "li", "tr", "h1", "h2", "h3"}
_WEB_SCHEMES = ("http://", "https://")


class _TextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.hidden_depth = 0
        self.parts: list[str] = []
        #: Destino del enlace abierto y posición de su texto en ``parts``.
        self.link: tuple[str, int] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in _HIDDEN:
            self.hidden_depth += 1
        elif self.hidden_depth:
            return
        elif tag in _BLOCKS:
            self.parts.append("\n")
        elif tag == "img":
            source = (dict(attrs).get("src") or "").strip()
            if source.lower().startswith("cid:") and len(source) > 4:
                self.parts.append(f"\n[cid:{source[4:]}]\n")
        elif tag == "a":
            target = (dict(attrs).get("href") or "").strip()
            web = target.lower().startswith(_WEB_SCHEMES) and not any(c.isspace() for c in target)
            self.link = (target, len(self.parts)) if web else None

    def handle_endtag(self, tag: str) -> None:
        if tag in _HIDDEN:
            self.hidden_depth = max(0, self.hidden_depth - 1)
        elif tag == "a" and self.link and not self.hidden_depth:
            target, start = self.link
            self.link = None
            if _comparable(target) not in _comparable("".join(self.parts[start:])):
                self.parts.append(f" <{target}>")

    def handle_data(self, data: str) -> None:
        if not self.hidden_depth:
            self.parts.append(data)


def _comparable(value: str) -> str:
    """Dirección sin esquema ni barra final, para saber si el texto del enlace ya la muestra."""
    lowered = value.strip().lower()
    for scheme in _WEB_SCHEMES:
        lowered = lowered.removeprefix(scheme)
    return lowered.rstrip("/")


def html_to_text(content: bytes | str) -> str:
    parser = _TextParser()
    parser.feed(
        content.decode("utf-8", errors="replace") if isinstance(content, bytes) else content
    )
    parser.close()
    return "".join(parser.parts).strip()
