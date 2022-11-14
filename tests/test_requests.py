def test_http():
    """HTTP/1.0でリクエストを送信する"""
    from src.browser import request

    URL = "http://example.org/"
    headers, body, option = request(URL)
    with open("tests/data/example.html", "r") as f:
        assert body == f.read()

def test_https():
    """HTTP/1.1でリクエストを送信する"""
    from src.browser import request

    URL = "https://example.org/"
    headers, body, option = request(URL)
    with open("tests/data/example.html", "r") as f:
        assert body == f.read()

def test_data_request():
    from src.browser import request

    headers, body, _ = request("data:text/html,Hello world")
    assert body == "Hello world"
    assert headers["content-type"] == "text/html"
