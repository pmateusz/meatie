#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler

import pytest
from http_test import HTTPTestServer
from meatie import endpoint
from meatie_aiohttp import Client


@pytest.mark.asyncio()
async def test_can_parse_string(http_server: HTTPTestServer) -> None:
    # GIVEN
    def handler(request: BaseHTTPRequestHandler) -> None:
        request.send_response(HTTPStatus.OK)
        request.end_headers()
        request.wfile.write(bytes([0xF0, 0x9F, 0x9A, 0x80]))

    http_server.handler = handler

    class TestClient(Client):
        @endpoint("/")
        async def get_response(self) -> str:
            ...

    # WHEN
    async with TestClient(http_server.create_session()) as client:
        response = await client.get_response()

    # THEN
    assert "🚀" == response


@pytest.mark.asyncio()
async def test_can_handle_invalid_encoding(http_server: HTTPTestServer) -> None:
    # GIVEN
    def handler(request: BaseHTTPRequestHandler) -> None:
        request.send_response(HTTPStatus.OK)
        request.send_header("Content-Type", "text/plain; charset=ascii")
        request.end_headers()
        request.wfile.write(bytes([0xF0, 0x9F, 0x9A, 0x80]))

    http_server.handler = handler

    class TestClient(Client):
        @endpoint("/")
        async def get_response(self) -> str:
            ...

    # WHEN
    async with TestClient(http_server.create_session()) as client:
        response = await client.get_response()

    # THEN
    assert "����" == response
