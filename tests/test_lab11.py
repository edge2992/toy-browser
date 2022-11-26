def test_opacity(mocker):
    from tests.util.mock import socket, ssl
    from src.graphics.browser import Browser

    _ = socket.patch(mocker)
    _ = ssl.patch(mocker)
    styles = "http://test.test/styles.css"
    socket.respond(
        styles,
        b"HTTP/1.0 200 OK\r\n"
        + b"content-type: text/css\r\n\r\n"
        + b"div { background-color:blue}",
    )
    size_and_opacity_url = "http://test.test/size_and_opacity"
    socket.respond(
        size_and_opacity_url,
        b"HTTP/1.0 200 OK\r\n"
        + b"content-type: text/html\r\n\r\n"
        + b"<link rel=stylesheet href='styles.css'>"
        + b'<div style="opacity:0.5"><div>Text</div></div>)',
    )

    browser = Browser()
    browser.load(size_and_opacity_url)
    browser.tab_surface.printTabCommands()


def test_multiply_difference(mocker):
    from tests.util.mock import socket, ssl
    from src.graphics.browser import Browser

    _ = socket.patch(mocker)
    _ = ssl.patch(mocker)

    styles = "http://test.test/styles.css"
    socket.respond(
        styles,
        b"HTTP/1.0 200 OK\r\n"
        + b"content-type: text/css\r\n\r\n"
        + b"div { background-color:blue}",
    )
    size_and_mix_blend_mode_url = "http://test.test/size_and_mix_blend_mode"
    socket.respond(
        size_and_mix_blend_mode_url,
        b"HTTP/1.0 200 OK\r\n"
        + b"content-type: text/html\r\n\r\n"
        + b"<link rel=stylesheet href='styles.css'>"
        + b'<div style="mix-blend-mode:multiply"><div>Mult</div></div>)'
        + b'<div style="mix-blend-mode:difference"><div>Diff</div></div>)',
    )

    browser = Browser()
    browser.load(size_and_mix_blend_mode_url)
    browser.tab_surface.printTabCommands()
