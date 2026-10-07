from app.services.body_text import html_to_text


def test_html_only_body_is_readable_without_scripts_or_remote_resources():
    body = (
        b"<html><head><title>hidden</title></head><body><p>Correo &amp; texto</p>"
        b'<script>fetch("https://external.test")</script><style>.hidden{}</style>'
        b'<img src="https://external.test/image.png"><p>Segundo</p></body></html>'
    )
    result = html_to_text(body)
    assert "Correo & texto" in result
    assert "Segundo" in result
    assert "fetch" not in result
    assert "external.test" not in result
    assert "hidden" not in result


def test_links_keep_their_real_destination_visible():
    body = (
        '<p>Revisa el <a href="https://contoso.example.test/informe?id=7">informe final</a>.</p>'
        '<p><a href="https://www.example.test/">https://www.example.test</a></p>'
        '<p><a href="mailto:ana@example.test">ana@example.test</a> y '
        '<a href="javascript:alert(1)">esto</a></p>'
    )
    result = html_to_text(body)
    assert "informe final <https://contoso.example.test/informe?id=7>." in result
    assert result.count("www.example.test") == 1
    assert "mailto" not in result
    assert "javascript" not in result


def test_linked_inline_image_keeps_marker_and_destination():
    result = html_to_text('<a href="https://www.example.test/"><img src="cid:logo@01"></a>')
    assert result.index("[cid:logo@01]") < result.index("<https://www.example.test/>")
