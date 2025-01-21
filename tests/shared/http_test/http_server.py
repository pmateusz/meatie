#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
import ssl
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from typing import Any, Optional

from typing_extensions import Self

from .handlers import Handler, RequestHandler


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
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Any,
    ) -> None:
        self.stop()


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
