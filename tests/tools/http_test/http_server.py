#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer, SimpleHTTPRequestHandler
from threading import Thread
from typing import Any, Callable, Optional

from aiohttp import ClientSession
from typing_extensions import Self

RequestHandler = Callable[[SimpleHTTPRequestHandler], None]


def _serve_forever(local_server: HTTPServer) -> None:
    with local_server:
        local_server.serve_forever()


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

    def run_in_background(self) -> None:
        server = HTTPServer(("localhost", 0), _create_handler_class(self), False)
        server.timeout = 0.5
        server.allow_reuse_address = True
        server.server_bind()
        server.server_activate()
        self.server = server

        thread = Thread(target=_serve_forever, args=(self.server,))
        thread.setDaemon(True)
        self.tread = thread
        self.tread.start()

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
        return ClientSession(base_url=f"http://localhost:{self.port}")


def _create_handler_class(server: HTTPTestServer) -> type[BaseHTTPRequestHandler]:
    class _TestHttpHandler(SimpleHTTPRequestHandler):
        def do_GET(self) -> None:
            if server.handler is None:
                self.send_response(HTTPStatus.INTERNAL_SERVER_ERROR)
                self.end_headers()
                self.wfile.write(b"handler is not set")
                return

            server.handler(self)

    return _TestHttpHandler
