import io

# from unittest import mock


class MockSocket:
    URLs = {}
    Requests = {}

    def __init__(self, *args, **kwargs):
        self.request = b""
        self.connected = False
        self.scheme = "http"
        self.ssl_hostname = None

    def connect(self, host_port):
        self.host, self.port = host_port
        self.connected = True
        self._check_cert()

    def _check_cert(self):
        if self.connected and self.host and self.ssl_hostname:
            assert (
                self.host == self.ssl_hostname
            ), "server_hostname does not match the host"
            if self.host.endswith(".badssl.com"):  # Fake badssl.com
                raise Exception("SSL Error")
                # raise ssl.SSLCertVerificationError()

    def send(self, text):
        self.request += text
        self.method, self.path, _ = self.request.decode("latin1").split(" ", 2)

        if self.method == "POST":
            beginning, self.body = self.request.decode("latin1").split("\r\n\r\n")
            headers = [item.split(": ") for item in beginning.split("\r\n")[1:]]
            assert any(name.lower() == "content-length" for name, value in headers)
            assert all(
                int(value) == len(self.body)
                for name, value in headers
                if name.lower() == "content-length"
            )

    def makefile(self, mode, encoding, newline):
        assert (
            self.connected and self.host and self.port
        ), "You cannot call makefile() on a socket until you call connect() and send()"
        if self.port == 80 and self.scheme == "http":
            url = self.scheme + "://" + self.host + self.path
        elif self.port == 443 and self.scheme == "https":
            url = self.scheme + "://" + self.host + self.path
        else:
            url = self.scheme + "://" + self.host + ":" + str(self.port) + self.path
        self.Requests.setdefault(url, []).append(self.request)
        assert (
            self.method == self.URLs[url][0]
        ), f"Made a {self.method} request to a {self.URLs[url][0]} URL"
        output = self.URLs[url][1]
        if self.URLs[url][2]:
            assert self.body == self.URLs[url][2], (self.body, self.URLs[url][2])
        return io.StringIO(output.decode(encoding).replace(newline, "\n"), newline)

    def close(self):
        self.connected = False

    @classmethod
    def respond(cls, url, response, method="GET", body=None):
        cls.URLs[url] = [method, response, body]

    @classmethod
    def respond_ok(cls, url, response, method="GET", body=None):
        response = ("HTTP/1.0 200 OK\r\n\r\n" + response).encode("utf8")
        cls.respond(url, response, method=method, body=body)

    @classmethod
    def made_request(cls, url):
        return url in cls.Requests

    @classmethod
    def last_request(cls, url):
        return cls.Requests[url][-1]

    @classmethod
    def clear_history(cls):
        cls.Requests = {}


class ssl:
    def wrap_socket(self, s, server_hostname):
        s.ssl_hostname = server_hostname
        s._check_cert()
        s.scheme = "https"
        return s
