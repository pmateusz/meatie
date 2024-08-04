#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
from decimal import Decimal
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler

import requests
from http_test import HTTPTestServer
from meatie import body, endpoint
from meatie_requests import Client


def test_use_custom_decoder(http_server: HTTPTestServer) -> None:
    # GIVEN response have json which will lose precision if parsed as float
    def handler(request: BaseHTTPRequestHandler) -> None:
        request.send_response(HTTPStatus.OK)
        request.send_header("Content-Type", "application/json")
        request.end_headers()
        request.wfile.write('{"foo": 42.000000000000001}'.encode("utf-8"))

    http_server.handler = handler

    def custom_json(response: requests.Response) -> dict[str, Decimal]:
        return response.json(parse_float=Decimal)

    class TestClient(Client):
        @endpoint(http_server.base_url + "/", body(json=custom_json))
        def get_response(self) -> dict[str, Decimal]:
            ...

    # WHEN
    with TestClient(requests.Session()) as client:
        response = client.get_response()

    # THEN
    assert {"foo": Decimal("42.000000000000001")} == response
