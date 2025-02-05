#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
from decimal import Decimal

import httpx
from http_test import HTTPTestServer
from http_test.handlers import MAGIC_NUMBER, magic_number
from httpx import Response

from meatie import body, endpoint
from meatie_httpx import Client


def test_use_custom_decoder(http_server: HTTPTestServer) -> None:
    # GIVEN response have json which will lose precision if parsed as float
    http_server.handler = magic_number

    def custom_json(response: Response) -> dict[str, Decimal]:
        return response.json(parse_float=Decimal)

    class TestClient(Client):
        @endpoint("/", body(json=custom_json))
        def get_response(self) -> dict[str, Decimal]: ...

    # WHEN
    with TestClient(httpx.Client(base_url=http_server.base_url)) as client:
        response = client.get_response()

    # THEN
    assert {"number": MAGIC_NUMBER} == response
