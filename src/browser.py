import gzip
import socket
import ssl
from typing import Dict, List, Tuple


def request(url: str) -> Tuple[Dict[str, str], str, List[str]]:
    option = []
    scheme, url = url.split(":", 1)
    assert scheme in [
        "http",
        "https",
        "data",
        "file",
        "view-source",
    ], "Unsupported scheme: {}".format(scheme)

    if scheme == "view-source":
        scheme, url = url.split(":", 1)
        assert scheme in [
            "http",
            "https",
            "data",
            "file",
        ], "Unsupported scheme: {}".format(scheme)
        option.append("view-source")

    if scheme == "data":
        content_type, body = url.split(r",", 1)
        return {"content-type": content_type}, body, option

    if scheme == "file":
        with open(url[2:], "r") as f:
            return {}, f.read(), option

    host, path = url.lstrip("//").split("/", 1)
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

    request_line: bytes
    if scheme == "http":
        request_line = "GET {} HTTP/1.0\r\n".format(path).encode("utf-8")
    else:
        request_line = "GET {} HTTP/1.1\r\n".format(path).encode("utf-8")

    header = {}
    header["Host"] = host
    header[
        "User-Agent"
    ] = "Mozilla/5.0 (X11; Linux x86_64; rv:78.0) Gecko/20100101 Firefox/78.0"
    header["Connection"] = "close"
    header["Accept-Encoding"] = "gzip"

    s.send(
        request_line
        + "\r\n".join("{}: {}".format(k, v) for k, v in header.items()).encode("utf-8")
        + "\r\n\r\n".encode("utf-8")
    )

    response = s.makefile("rb", newline="\r\n")
    statusline = response.readline().decode("utf-8")
    version, status, explanation = statusline.split(" ", 2)
    assert status == "200", "{}: {}".format(status, explanation)

    headers = {}
    while True:
        line = response.readline().decode("utf-8")
        if line == "\r\n":
            break
        header, value = line.split(":", 1)
        headers[header.lower()] = value.strip()

    if "transfer-encoding" not in headers:
        raw_body = response.read()
    else:
        assert headers["transfer-encoding"] == "chunked"
        # TODO:未確認
        print("transfer-encoding: chunked!")
        raw_body = chunked_reader(response)

    if "content-encoding" in headers:
        assert headers["content-encoding"] == "gzip"
        # gzip形式のデータをTransfer-Encodingのチャンクで受信する
        print("gziped file!")
        raw_body = gzip.decompress(raw_body)

    body = raw_body.decode("utf-8")
    s.close()
    return headers, body, option


def chunked_reader(response):
    body = b""
    while response.readline.decode("utf-8") != 0:
        body += response.readline
    return body


def show(body: str, option: List[str]) -> None:
    if "view-source" in option:
        print(body)
    else:
        print(transform(body))


def transform(body: str) -> str:
    in_angle = False
    out_angle = False
    in_entity = False
    entity = ""
    out = ""
    tags = []

    ENTRY_DICT = {
        "lt": "<",
        "gt": ">",
    }

    for c in body:
        if c == "<":
            in_angle = True
            tags.append("")
        elif c == ">":
            in_angle = False
            out_angle = False
        elif in_angle and c == "/":
            out_angle = True
            tags.pop()
        elif in_angle and (not out_angle):
            tags[len(tags) - 1] += c
        elif c == "&":
            in_entity = True
            entity = ""
        elif in_entity:
            if c == ";":
                if "body" in tags:
                    out += ENTRY_DICT[entity]
                in_entity = False
            else:
                entity += c
        elif not in_angle and "body" in tags:
            out += c
    return out


def load(url: str) -> None:
    headers, body, option = request(url)
    show(body, option)


if __name__ == "__main__":
    import sys

    load(sys.argv[1])