import socket
from typing import Dict, Tuple


def request(url: str) -> Tuple[Dict[str, str], str]:
    assert url.startswith("http://")
    url = url[len("http://") :]
    host, path = url.split("/", 1)
    path = "/" + path

    s = socket.socket(
        family=socket.AF_INET, type=socket.SOCK_STREAM, proto=socket.IPPROTO_TCP
    )

    s.connect((host, 80))

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
