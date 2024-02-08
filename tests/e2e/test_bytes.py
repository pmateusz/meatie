#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler

import pytest
from http_test import HTTPTestServer
from meatie import endpoint
from meatie.adapter import BytesAdapter
from meatie_aiohttp import AiohttpClient

SAMPLE_BYTES = b"Hello, world!"


@pytest.mark.asyncio()
async def test_can_parse_bytes(http_server: HTTPTestServer) -> None:
    # GIVEN
    def handler(request: BaseHTTPRequestHandler) -> None:
        request.send_response(HTTPStatus.OK)
        request.end_headers()
        request.wfile.write(SAMPLE_BYTES)

    http_server.handler = handler

    class TestClient(AiohttpClient):
        @endpoint("/")
        async def get_response(self) -> bytes:
            ...

    # WHEN
    async with TestClient(http_server.create_session()) as client:
        response = await client.get_response()

    # THEN
    assert SAMPLE_BYTES == response


def test_to_json() -> None:
    # WHEN
    result = BytesAdapter.to_json(SAMPLE_BYTES)

    # THEN
    assert SAMPLE_BYTES == result
