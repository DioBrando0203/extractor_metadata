"""Convierte un cuerpo HTML a texto sin ejecutar contenido ni resolver recursos.

Las imágenes incrustadas (``<img src="cid:…">``) se conservan como marcadores ``[cid:…]`` en su
posición, la misma convención que Outlook usa en el cuerpo de texto plano. Imágenes remotas y
cualquier otro recurso externo se descartan.
"""

from html.parser import HTMLParser

_HIDDEN = {"script", "style", "head"}
_BLOCKS = {"br", "p", "div", "li", "tr", "h1", "h2", "h3"}


class _TextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.hidden_depth = 0
        self.parts: list[str] = []

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

    def handle_endtag(self, tag: str) -> None:
        if tag in _HIDDEN:
            self.hidden_depth = max(0, self.hidden_depth - 1)

    def handle_data(self, data: str) -> None:
        if not self.hidden_depth:
            self.parts.append(data)


def html_to_text(content: bytes | str) -> str:
    parser = _TextParser()
    parser.feed(
        content.decode("utf-8", errors="replace") if isinstance(content, bytes) else content
    )
    parser.close()
    return "".join(parser.parts).strip()
