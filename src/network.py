import gzip
import socket
import ssl
from typing import Dict, List, Tuple, Union

COOKIE_JAR: Dict[str, Tuple[str, Dict]] = {}


def request(
    url: str,
    top_level_url: Union[str, None],
    payload: Union[str, None] = None,
    max_redirs: int = 50,
) -> Tuple[Dict[str, str], str, List[str]]:
    if max_redirs == 0:
        raise Exception("Too many redirects")

    option: List[str] = []
    method: str = "POST" if payload else "GET"
    scheme, url = url.split(":", 1)

    assert scheme in [
        "http",
        "https",
        "data",
        "file",
        "view-source",
    ], "Unsupported scheme: {}".format(scheme)

    if scheme == "data":
        content_type, body = url.split(r",", 1)
        return {"content-type": content_type}, body, option

    if scheme == "file":
        with open(url[2:], "r") as f:
            return {}, f.read(), option

    if scheme == "view-source":
        scheme, url = url.split(":", 1)
        assert scheme in [
            "http",
            "https",
            "data",
            "file",
        ], "Unsupported scheme: {}".format(scheme)
        option.append("view-source")

    host, path = url.lstrip("//").split("/", 1)
    path = "/" + path

    port = 80 if scheme == "http" else 443

    # example: http://example.org:8080/foo/bar
    if ":" in host:
        host, port_str = host.split(":", 1)
        port = int(port_str)

    with socket.socket(
        family=socket.AF_INET, type=socket.SOCK_STREAM, proto=socket.IPPROTO_TCP
    ) as sock:
        if scheme == "https":
            ctx = ssl.create_default_context()
            with ctx.wrap_socket(sock, server_hostname=host) as ssock:
                headers, body = _get_headers_and_body(
                    ssock,
                    method,
                    host,
                    port,
                    path,
                    scheme,
                    top_level_url,
                    payload,
                    max_redirs,
                )
                return headers, body, option
        headers, body = _get_headers_and_body(
            sock, method, host, port, path, scheme, top_level_url, payload, max_redirs
        )
        return headers, body, option


def _get_headers_and_body(
    sock: socket.socket,
    method: str,
    host: str,
    port: int,
    path: str,
    scheme: str,
    top_level_url: Union[str, None],
    payload: Union[str, None],
    max_redirs: int,
):
    sock.connect((host, port))

    headers: Dict[str, str] = {}
    headers["Host"] = host
    headers[
        "User-Agent"
    ] = "Mozilla/5.0 (X11; Linux x86_64; rv:78.0) Gecko/20100101 Firefox/78.0"
    headers["Connection"] = "close"
    headers["Accept-Encoding"] = "gzip"
    if method == "POST":
        assert payload is not None
        headers["Content-Length"] = str(len(payload.encode("utf-8")))

    version = "HTTP/1.1" if scheme == "https" else "HTTP/1.0"

    body = "{} {} {}\r\n".format(method, path, version)
    body += "\r\n".join("{}: {}".format(k, v) for k, v in headers.items()) + "\r\n"
    if host in COOKIE_JAR:
        cookie, params = COOKIE_JAR[host]
        allow_cookie: bool = True
        if top_level_url and params.get("samesite", "none") == "lax":
            _, _, top_level_host, _ = top_level_url.split("/", 3)
            if ":" in top_level_host:
                top_level_host, _ = top_level_host.split(":", 1)
            allow_cookie = host == top_level_host or method == "GET"
        if allow_cookie:
            body += "Cookie: {}\r\n".format(cookie)
    body += "\r\n" + (payload or "")

    sock.send(body.encode("utf-8"))

    response = sock.makefile("rb", newline="\r\n")
    statusline = response.readline().decode("utf-8")
    version, status, explanation = statusline.split(" ", 2)
    assert status in ("200", "301", "302"), "Unsupported status: {}\n{}".format(
        status, explanation
    )

    headers = {}
    while True:
        line = response.readline().decode("utf-8")
        if line == "\r\n":
            break
        header, value = line.split(":", 1)
        headers[header.lower()] = value.strip()

    if "location" in headers:
        headers, body, option = request(
            headers["location"], headers["location"], max_redirs=max_redirs - 1
        )
        return headers, body

    if "set-cookie" in headers:
        params = {}
        if ";" in headers["set-cookie"]:
            cookie, rest = headers["set-cookie"].split(";", 1)
            for param_pair in rest.split(";"):
                name, value = param_pair.split("=", 1)
                params[name.lower()] = value.lower()
        else:
            cookie = headers["set-cookie"]
        COOKIE_JAR[host] = (cookie, params)

    if "transfer-encoding" in headers:
        if headers["transfer-encoding"] == "chunked":
            print("transfer-encoding: chunked!")
            body_b = unchunked(response)
        else:
            raise Exception(
                "Unsupported transfer-encoding: {}".format(headers["transfer-encoding"])
            )
    else:
        body_b = response.read()

    if "content-encoding" in headers:
        assert headers["content-encoding"] == "gzip"
        # gzip形式のデータをTransfer-Encodingのチャンクで受信する
        print("gziped file!")
        body_b = gzip.decompress(body_b)

    body = body_b.decode("utf-8")
    sock.close()
    return headers, body


def unchunked(response):
    body = b""

    def get_chunk_size():
        chunk_size = response.readline().rstrip()
        return int(chunk_size, 16)

    while True:
        chunk_size = get_chunk_size()
        if chunk_size == 0:
            break
        else:
            body += response.read(chunk_size)
            response.read(2)
    return body


def show(body: str, option: List[str]) -> None:
    if "view-source" in option:
        print(body)
    else:
        print(lex(body))


def lex(body: str) -> str:
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
            if not out_angle:
                # TODO: classやidも保存する
                tags[len(tags) - 1] = tags[len(tags) - 1].split()[0]
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
    headers, body, option = request(url, url)
    show(body, option)


if __name__ == "__main__":
    import sys

    load(sys.argv[1])
