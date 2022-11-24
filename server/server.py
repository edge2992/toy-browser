import random
import socket
import urllib.parse
from typing import Dict, Tuple, Union

s = socket.socket(
    family=socket.AF_INET, type=socket.SOCK_STREAM, proto=socket.IPPROTO_TCP
)

s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

s.bind(("", 8000))
s.listen()

ENTRIES = [
    ("No names. We are nameless!", "cerealkiller"),
    ("HACK THE PLANET", "crashoverride"),
]

LOGINS: Dict[str, str] = {
    "crashoverride": "Ocool",
    "cerealkiller": "emmanuel",
}
SESSIONS: Dict[str, Dict] = {}


def show_comments(session: Dict) -> str:
    out = "<!dotctype html>"
    out += "<head>"
    out += "<link rel='stylesheet' href='/comment.css'>"
    out += "</head>"
    out += "<script src=/comment.js></script>"
    if "user" in session:
        out += "<h1>Hello, " + session["user"] + "</h1>"
        out += "<form action=add method=post>"
        out += "<p><input name=guest></p>"
        out += "<label></label>"
        out += "<p><button>Sign the book!</button></p>"
        out += "</form>"
    else:
        out += "<a href=/login>Sign in to write in the guest book</a>"
    for entry, who in ENTRIES:
        out += "<p>{entry}\n<i>by {who}</i></p>"

    return out


def login_form(session: Dict):
    out = "<!doctype html>"
    out += "<form action=/ method=post>"
    out += "<p>Username: <input name=username></p>"
    out += "<p>Password: <input name=password type=password></p>"
    out += "<p><button>Log in</button></p>"
    out += "</form>"
    return out


def do_login(session: Dict, params: Dict):
    username = params.get("username")
    password = params.get("password")
    if username and password and username in LOGINS and LOGINS[username] == password:
        session["user"] = username
        return "200 OK", show_comments(session)
    else:
        out = "<!doctype html>"
        out += "<h1>Invalid username or password</h1>"
        return "401 Unauthorized", out


def form_decode(body: str) -> Dict:
    params = {}
    for field in body.split("&"):
        name, value = field.split("=", 1)
        name = urllib.parse.unquote_plus(name)
        value = urllib.parse.unquote_plus(value)
        params[name] = value
    return params


def add_entry(session: Dict, params: Dict):
    if "user" not in session:
        return
    if "guest" in params and len(params["guest"]) <= 100:
        ENTRIES.append((params["guest"], session["user"]))


def not_found(url: str, method: str) -> str:
    out = "<!doctype html>"
    out += "<h1>{} {} not found</h1>".format(method, url)
    return out


def do_request(
    session: Dict, method: str, url: str, headers: Dict, body: Union[str, None]
) -> Tuple[str, str]:
    if method == "GET" and url == "/":
        return "200 OK", show_comments(session)
    elif method == "GET" and url == "/login":
        return "200 OK", login_form(session)
    elif method == "GET" and url == "/comment.js":
        with open("server/comment.js", "r") as f:
            return "200 OK", f.read()
    elif method == "GET" and url == "/comment.css":
        with open("server/comment.css", "r") as f:
            return "200 OK", f.read()
    elif method == "POST" and url == "/add":
        assert body is not None
        params = form_decode(body)
        add_entry(session, params)
        return "200 OK", show_comments(session)
    elif method == "POST" and url == "/":
        assert body is not None
        params = form_decode(body)
        return do_login(session, params)
    else:
        return "404 Not Found", not_found(url, method)


def handle_connection(conx: socket.socket):
    req = conx.makefile("rb")
    reqline = req.readline().decode("utf-8")
    method, url, version = reqline.split(" ", 2)
    assert method in ["GET", "POST"]
    headers = {}
    while True:
        line = req.readline().decode("utf-8")
        if line == "\r\n":
            break
        header, value = line.split(":", 1)
        headers[header.lower()] = value.strip()

    if "content-length" in headers:
        length = int(headers["content-length"])
        body = req.read(length).decode("utf-8")
    else:
        body = None

    token: str
    if "cookie" in headers:
        token = headers["cookie"][len("token=") :]
    else:
        token = str(random.random())[2:]

    session = SESSIONS.setdefault(token, {})
    status, body = do_request(session, method, url, headers, body)

    assert isinstance(body, str)
    response = "HTTP/1.0 {}\r\n".format(status)
    response += "Context-Length: {}\r\n".format(len(body.encode("utf-8")))
    if "cookie" not in headers:
        response += "Set-Cookie: token={}\r\n".format(token)
    response += "\r\n" + body
    conx.send(response.encode("utf-8"))
    conx.close()


while True:
    conx, addr = s.accept()
    handle_connection(conx)
