"""Convierte un cuerpo HTML a texto sin ejecutar contenido ni resolver recursos."""

from html.parser import HTMLParser


class _TextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.hidden_depth = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "head"}:
            self.hidden_depth += 1
        elif tag in {"br", "p", "div", "li", "tr", "h1", "h2", "h3"} and not self.hidden_depth:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "head"}:
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
