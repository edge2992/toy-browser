import socket
import ssl
from typing import Dict, Tuple


def request(url: str) -> Tuple[Dict[str, str], str]:
    scheme, url = url.split("://", 1)
    assert scheme in ["http", "https"], "Unsupported scheme: {}".format(scheme)

    host, path = url.split("/", 1)
    path = "/" + path

    port = 80 if scheme == "http" else 443

    # example: http://example.org:8080/foo/bar
    if ":" in host:
        host, port = host.split(":", 1)
        port = int(port)

    s = socket.socket(
        family=socket.AF_INET, type=socket.SOCK_STREAM, proto=socket.IPPROTO_TCP
    )

    if scheme == "https":
        ctx = ssl.create_default_context()
        s = ctx.wrap_socket(s, server_hostname=host)

    s.connect((host, port))

    s.send(
        "GET {} HTTP/1.0\r\n".format(path).encode("utf-8")
        + "HOST: {}\r\n\r\n".format(host).encode("utf-8")
    )

    response = s.makefile("r", encoding="utf-8", newline="\r\n")
    statusline = response.readline()
    version, status, explanation = statusline.split(" ", 2)
    assert status == "200", "{}: {}".format(status, explanation)

    headers = {}
    while True:
        line = response.readline()
        if line == "\r\n":
            break
        header, value = line.split(":", 1)
        headers[header.lower()] = value.strip()

    assert "transfer-encoding" not in headers
    assert "content-encoding" not in headers

    body = response.read()
    s.close()
    return headers, body


def show(body: str) -> None:
    in_angle = False
    for c in body:
        if c == "<":
            in_angle = True
        elif c == ">":
            in_angle = False
        elif not in_angle:
            print(c, end="")


def load(url: str) -> None:
    headers, body = request(url)
    show(body)


if __name__ == "__main__":
    import sys

    load(sys.argv[1])
