#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
import json
import ssl
import urllib.parse
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer, SimpleHTTPRequestHandler
from threading import Thread
from typing import Any, Callable, Optional

from aiohttp import ClientSession
from typing_extensions import Self


class Handler(SimpleHTTPRequestHandler):
    def send_json(self, status_code: HTTPStatus, message: Any) -> None:
        try:
            json_message = json.dumps(message)
        except Exception as exc:
            self.send_text(
                HTTPStatus.INTERNAL_SERVER_ERROR, "Failed to serialize response: " + str(exc)
            )
            return

        self.send_bytes(status_code, "application/json", json_message.encode("utf-8"))

    def send_text(self, status_code: HTTPStatus, text: str) -> None:
        self.send_bytes(status_code, "text/plain", text.encode("utf-8"))

    def send_bytes(self, status_code: HTTPStatus, content_type: str, message: bytes) -> None:
        self.send_response(status_code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(message)))
        self.end_headers()
        self.wfile.write(message)

    def safe_content_length(self) -> Optional[int]:
        content_length_raw = self.headers.get("Content-Length", "0")
        try:
            return int(content_length_raw)
        except ValueError:
            self.send_text(
                HTTPStatus.BAD_REQUEST,
                f"Content length should be an integer: '{content_length_raw}'",
            )
            return None

    def safe_bytes(self) -> Optional[bytes]:
        content_length_opt = self.safe_content_length()
        if content_length_opt is None:
            return None

        try:
            return self.rfile.read(content_length_opt)
        except Exception as exc:
            self.send_text(HTTPStatus.BAD_REQUEST, "Failed to read request body: " + str(exc))
            return None

    def safe_text(self) -> Optional[str]:
        raw_body_opt = self.safe_bytes()
        if raw_body_opt is None:
            return None

        content_charset = self.headers.get_content_charset("utf-8")
        try:
            return raw_body_opt.decode(content_charset)
        except Exception as exc:
            self.send_text(HTTPStatus.BAD_REQUEST, "Failed to decode request body: " + str(exc))
            return None


RequestHandler = Callable[[Handler], None]


class StatusHandler:
    def __init__(self, status: HTTPStatus) -> None:
        self.status = status

    def __call__(self, handler: Handler) -> None:
        handler.send_response(self.status)
        handler.end_headers()


def echo_handler(handler: Handler) -> None:
    raw_body_opt = handler.safe_bytes()
    if raw_body_opt is None:
        return

    content_type = handler.headers.get_content_type()
    handler.send_bytes(HTTPStatus.OK, content_type, raw_body_opt)


def diagnostic_handler(handler: Handler) -> None:
    body_opt = handler.safe_text()
    if body_opt is None:
        return

    headers = {key: value for key, value in handler.headers.items()}
    try:
        url = urllib.parse.urlparse(handler.path)
    except Exception as exc:
        handler.send_text(HTTPStatus.BAD_REQUEST, "Failed to parse URL: " + str(exc))
        return

    response = {
        "path": url.path,
        "scheme": url.scheme,
        "params": url.params,
        "query": url.query,
        "fragment": url.fragment,
        "netloc": url.netloc,
        "headers": headers,
        "body": body_opt,
    }
    handler.send_json(HTTPStatus.OK, response)


class HTTPTestServer:
    def __init__(self) -> None:
        self.handler: Optional[RequestHandler] = None
        self.server: Optional[HTTPServer] = None
        self.tread: Optional[Thread] = None

    @property
    def port(self) -> int:
        if self.server is None:
            raise RuntimeError("server is not started")

        return self.server.server_port

    @property
    def base_url(self) -> str:
        return f"http://localhost:{self.port}"

    def run_in_background(self) -> None:
        server = HTTPServer(("localhost", 0), _create_handler_class(self), False)
        self.configure(server)
        server.server_bind()
        server.server_activate()
        self.server = server

        thread = Thread(target=_serve_forever, args=(self.server,))
        thread.daemon = True
        self.tread = thread
        self.tread.start()

    def configure(self, server: HTTPServer) -> None:
        server.timeout = 0.5
        server.allow_reuse_address = True

    def stop(self) -> None:
        if self.server is not None:
            try:
                self.server.shutdown()
            finally:
                self.server = None

        if self.tread is not None:
            try:
                self.tread.join()
            finally:
                self.tread = None

    def __enter__(self) -> Self:
        self.run_in_background()
        return self

    def __exit__(
        self, exc_type: Optional[type[BaseException]], exc_val: Optional[BaseException], exc_tb: Any
    ) -> None:
        self.stop()

    def create_session(self) -> ClientSession:
        return ClientSession(base_url=self.base_url)


class HTTPSTestServer(HTTPTestServer):
    def __init__(self, context: ssl.SSLContext) -> None:
        super().__init__()

        self.context = context

    def configure(self, server: HTTPServer) -> None:
        super().configure(server)

        server.socket = self.context.wrap_socket(
            server.socket,
            server_side=True,
        )

    @property
    def base_url(self) -> str:
        return f"https://localhost:{self.port}"


def _create_handler_class(server: HTTPTestServer) -> type[BaseHTTPRequestHandler]:
    class _TestHttpHandler(Handler):
        def do_GET(self) -> None:
            self.call_handler()

        def do_POST(self) -> None:
            self.call_handler()

        def call_handler(self) -> Optional[RequestHandler]:
            if server.handler is None:
                self.send_text(HTTPStatus.INTERNAL_SERVER_ERROR, "handler is not set")
                return None

            server.handler(self)

    return _TestHttpHandler


def _serve_forever(local_server: HTTPServer) -> None:
    with local_server:
        local_server.serve_forever()
