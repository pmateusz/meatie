#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
import json
from decimal import Decimal
from functools import partial
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler

import pytest
from http_test import HTTPTestServer
from meatie import ParseResponseError, endpoint
from meatie_aiohttp import Client
from typing_extensions import override


@pytest.mark.asyncio()
async def test_can_parse_json(http_server: HTTPTestServer) -> None:
    # GIVEN
    def handler(request: BaseHTTPRequestHandler) -> None:
        request.send_response(HTTPStatus.OK)
        request.send_header("Content-Type", "application/json")
        request.end_headers()
        request.wfile.write('{"status": "ok"}'.encode("utf-8"))

    http_server.handler = handler

    class TestClient(Client):
        @endpoint("/")
        async def get_response(self) -> dict[str, str]:
            ...

    # WHEN
    async with TestClient(http_server.create_session()) as client:
        response = await client.get_response()

    # THEN
    assert {"status": "ok"} == response


@pytest.mark.asyncio()
async def test_can_handle_invalid_content_type(http_server: HTTPTestServer) -> None:
    # GIVEN
    content = "{'status': 'ok'}"

    def handler(request: BaseHTTPRequestHandler) -> None:
        request.send_response(HTTPStatus.OK)
        request.end_headers()
        request.wfile.write(content.encode("utf-8"))

    http_server.handler = handler

    class TestClient(Client):
        @endpoint("/")
        async def get_response(self) -> dict[str, str]:
            ...

    # WHEN
    with pytest.raises(ParseResponseError) as exc_info:
        async with TestClient(http_server.create_session()) as client:
            await client.get_response()

    # THEN
    exc = exc_info.value
    assert content == exc.text
    assert 0 == exc.response.status


@pytest.mark.asyncio()
async def test_can_handle_corrupted_json(http_server: HTTPTestServer) -> None:
    # GIVEN
    def handler(request: BaseHTTPRequestHandler) -> None:
        request.send_response(HTTPStatus.OK)
        request.send_header("Content-Type", "application/json")
        request.end_headers()
        request.wfile.write("{'status':".encode("utf-8"))

    http_server.handler = handler

    class TestClient(Client):
        @endpoint("/")
        async def get_response(self) -> dict[str, str]:
            ...

    # WHEN
    with pytest.raises(ParseResponseError) as exc_info:
        async with TestClient(http_server.create_session()) as client:
            await client.get_response()

    # THEN
    exc = exc_info.value
    assert HTTPStatus.OK == exc.response.status


@pytest.mark.asyncio()
async def test_can_configure_json_loads(http_server: HTTPTestServer) -> None:
    # GIVEN response have json which will lose precision if parsed as float
    raw_json = '{"foo": 42.000000000000001}'
    assert json.dumps(json.loads(raw_json)) != raw_json

    def handler(request: BaseHTTPRequestHandler) -> None:
        request.send_response(HTTPStatus.OK)
        request.send_header("Content-Type", "application/json")
        request.end_headers()
        request.wfile.write(raw_json.encode("utf-8"))

    http_server.handler = handler

    class TestClient(Client):
        @classmethod
        @override
        def loads(cls) -> json.JSONDecoder:
            return partial(json.loads, parse_float=Decimal)

        @endpoint("/")
        async def get_response(self) -> dict[str, Decimal]:
            ...

    # WHEN
    async with TestClient(http_server.create_session()) as client:
        response = await client.get_response()

    # THEN
    assert {"foo": Decimal("42.000000000000001")} == response
