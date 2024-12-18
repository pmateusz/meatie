#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler

import httpx
import pytest
from http_test import HTTPTestServer
from meatie import HttpStatusError, Response, ResponseError, body, endpoint
from meatie_httpx import Client


def get_error(response: Response) -> Exception | None:
    exc_type = HttpStatusError if response.status >= 300 else ResponseError

    body = response.json()
    if isinstance(body, dict):
        error = body.get("error")
        if error is not None:
            return exc_type(response, error)

    if response.status >= 300:
        return exc_type(response)

    return None


def test_raises_error(http_server: HTTPTestServer) -> None:
    # GIVEN
    def handler(request: BaseHTTPRequestHandler) -> None:
        request.send_response(HTTPStatus.SERVICE_UNAVAILABLE)
        request.send_header("Content-Type", "application/json")
        request.end_headers()
        request.wfile.write('{"error": "deployment in progress"}'.encode("utf-8"))

    http_server.handler = handler

    class TestClient(Client):
        @endpoint("/", body(error=get_error))
        def get_response(self) -> dict[str, str]:
            ...

    # WHEN
    with pytest.raises(HttpStatusError) as exc_info:
        with TestClient(httpx.Client(base_url=http_server.base_url)) as client:
            client.get_response()

    # THEN
    assert exc_info.value.args == ("deployment in progress",)
