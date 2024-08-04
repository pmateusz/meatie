#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
from decimal import Decimal
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler

import httpx
from http_test import HTTPTestServer
from httpx import Response
from meatie import body, endpoint
from meatie_httpx import Client


def test_use_custom_decoder(http_server: HTTPTestServer) -> None:
    # GIVEN response have json which will lose precision if parsed as float
    def handler(request: BaseHTTPRequestHandler) -> None:
        request.send_response(HTTPStatus.OK)
        request.send_header("Content-Type", "application/json")
        request.end_headers()
        request.wfile.write('{"foo": 42.000000000000001}'.encode("utf-8"))

    http_server.handler = handler

    def custom_json(response: Response) -> dict[str, Decimal]:
        return response.json(parse_float=Decimal)

    class TestClient(Client):
        @endpoint("/", body(json=custom_json))
        def get_response(self) -> dict[str, Decimal]:
            ...

    # WHEN
    with TestClient(httpx.Client(base_url=http_server.base_url)) as client:
        response = client.get_response()

    # THEN
    assert {"foo": Decimal("42.000000000000001")} == response
