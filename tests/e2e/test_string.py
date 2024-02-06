#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler

import pytest
from http_test import HTTPTestServer
from meatie.aio import endpoint
from meatie.error import ParseResponseError
from meatie_aiohttp import AiohttpClient


@pytest.mark.asyncio()
async def test_can_parse_string(test_server: HTTPTestServer) -> None:
    # GIVEN
    def handler(request: BaseHTTPRequestHandler) -> None:
        request.send_response(HTTPStatus.OK)
        request.end_headers()
        request.wfile.write(bytes([0xF0, 0x9F, 0x9A, 0x80]))

    test_server.handler = handler

    class TestClient(AiohttpClient):
        @endpoint("/")
        async def get_response(self) -> str:
            ...

    # WHEN
    async with TestClient(test_server.create_session()) as client:
        response = await client.get_response()

    # THEN
    assert "🚀" == response


@pytest.mark.asyncio()
async def test_can_handle_invalid_encoding(test_server: HTTPTestServer) -> None:
    # GIVEN
    def handler(request: BaseHTTPRequestHandler) -> None:
        request.send_response(HTTPStatus.OK)
        request.send_header("Content-Type", "text/plain; charset=ascii")
        request.end_headers()
        request.wfile.write(bytes([0xF0, 0x9F, 0x9A, 0x80]))

    test_server.handler = handler

    class TestClient(AiohttpClient):
        @endpoint("/")
        async def get_response(self) -> str:
            ...

    # WHEN
    with pytest.raises(ParseResponseError) as exc_info:
        async with TestClient(test_server.create_session()) as client:
            await client.get_response()

    # THEN
    exc = exc_info.value
    assert HTTPStatus.OK == exc.response.status
