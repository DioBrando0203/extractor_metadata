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
