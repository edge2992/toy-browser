def test_http():
    """HTTP/1.0でリクエストを送信する"""
    from src.network import request

    URL = "http://example.org/"
    headers, body, option = request(URL, None)
    with open("tests/data/example.html", "r") as f:
        assert body == f.read()


def test_https():
    """HTTP/1.1でリクエストを送信する"""
    from src.network import request

    URL = "https://example.org/"
    headers, body, option = request(URL, None)
    with open("tests/data/example.html", "r") as f:
        assert body == f.read()


def test_data_request():
    from src.network import request

    headers, body, _ = request("data:text/html,Hello world", None)
    assert body == "Hello world"
    assert headers["content-type"] == "text/html"


def test_redirect():
    """リダイレクトを処理する"""
    from src.network import request

    headers, body, _ = request("http://browser.engineering/redirect", None)
    assert len(body) > 0
    assert "content-type" in headers
