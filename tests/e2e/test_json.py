#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler

import pytest
from http_test import HTTPTestServer
from meatie import ParseResponseError, endpoint
from meatie_aiohttp import AiohttpClient


@pytest.mark.asyncio()
async def test_can_parse_json(test_server: HTTPTestServer) -> None:
    # GIVEN
    def handler(request: BaseHTTPRequestHandler) -> None:
        request.send_response(HTTPStatus.OK)
        request.send_header("Content-Type", "application/json")
        request.end_headers()
        request.wfile.write('{"status": "ok"}'.encode("utf-8"))

    test_server.handler = handler

    class TestClient(AiohttpClient):
        @endpoint("/")
        async def get_response(self) -> dict[str, str]:
            ...

    # WHEN
    async with TestClient(test_server.create_session()) as client:
        response = await client.get_response()

    # THEN
    assert {"status": "ok"} == response


@pytest.mark.asyncio()
async def test_can_handle_invalid_content_type(test_server: HTTPTestServer) -> None:
    # GIVEN
    content = "{'status': 'ok'}"

    def handler(request: BaseHTTPRequestHandler) -> None:
        request.send_response(HTTPStatus.OK)
        request.end_headers()
        request.wfile.write(content.encode("utf-8"))

    test_server.handler = handler

    class TestClient(AiohttpClient):
        @endpoint("/")
        async def get_response(self) -> dict[str, str]:
            ...

    # WHEN
    with pytest.raises(ParseResponseError) as exc_info:
        async with TestClient(test_server.create_session()) as client:
            await client.get_response()

    # THEN
    exc = exc_info.value
    assert content == exc.text
    assert 0 == exc.response.status


@pytest.mark.asyncio()
async def test_can_handle_corrupted_json(test_server: HTTPTestServer) -> None:
    # GIVEN
    def handler(request: BaseHTTPRequestHandler) -> None:
        request.send_response(HTTPStatus.OK)
        request.send_header("Content-Type", "application/json")
        request.end_headers()
        request.wfile.write("{'status':".encode("utf-8"))

    test_server.handler = handler

    class TestClient(AiohttpClient):
        @endpoint("/")
        async def get_response(self) -> dict[str, str]:
            ...

    # WHEN
    with pytest.raises(ParseResponseError) as exc_info:
        async with TestClient(test_server.create_session()) as client:
            await client.get_response()

    # THEN
    exc = exc_info.value
    assert HTTPStatus.OK == exc.response.status
