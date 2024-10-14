#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
import json
from decimal import Decimal
from functools import partial
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler

import pytest
from aiohttp import ClientResponse
from http_test import HTTPTestServer
from meatie import ParseResponseError, body, endpoint
from meatie_aiohttp import Client
from aiohttp import ClientSession


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
    async with TestClient(ClientSession(http_server.base_url)) as client:
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
        async with TestClient(ClientSession(http_server.base_url)) as client:
            await client.get_response()

    # THEN
    exc = exc_info.value
    assert content == exc.text
    assert HTTPStatus.OK == exc.response.status


@pytest.mark.asyncio()
async def test_can_handle_html_response(http_server: HTTPTestServer) -> None:
    # GIVEN
    content = (
        "<html>"
        "<head><title>504 Gateway Time-out</title></head>"
        "<body><center><h1>504 Gateway Time-out</h1></center><hr><center>nginx</center></body>"
        "</html>"
    )

    def handler(request: BaseHTTPRequestHandler) -> None:
        request.send_response(HTTPStatus.GATEWAY_TIMEOUT)
        request.send_header("Content-Type", "text/html")
        request.end_headers()
        request.wfile.write(content.encode("utf-8"))

    http_server.handler = handler

    class TestClient(Client):
        @endpoint("/")
        async def get_response(self) -> dict[str, str]:
            ...

    # WHEN
    with pytest.raises(ParseResponseError) as exc_info:
        async with TestClient(ClientSession(http_server.base_url)) as client:
            await client.get_response()

    # THEN
    exc = exc_info.value
    assert content == exc.text
    assert HTTPStatus.GATEWAY_TIMEOUT == exc.response.status


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
        async with TestClient(ClientSession(http_server.base_url)) as client:
            await client.get_response()

    # THEN
    exc = exc_info.value
    assert HTTPStatus.OK == exc.response.status


@pytest.mark.asyncio()
async def test_use_custom_decoder(http_server: HTTPTestServer) -> None:
    # GIVEN response have json which will lose precision if parsed as float
    def handler(request: BaseHTTPRequestHandler) -> None:
        request.send_response(HTTPStatus.OK)
        request.send_header("Content-Type", "application/json")
        request.end_headers()
        request.wfile.write('{"foo": 42.000000000000001}'.encode("utf-8"))

    http_server.handler = handler

    async def custom_json(response: ClientResponse) -> dict[str, Decimal]:
        return await response.json(loads=partial(json.loads, parse_float=Decimal))

    class TestClient(Client):
        @endpoint("/", body(json=custom_json))
        async def get_response(self) -> dict[str, Decimal]:
            ...

    # WHEN
    async with TestClient(ClientSession(http_server.base_url)) as client:
        response = await client.get_response()

    # THEN
    assert {"foo": Decimal("42.000000000000001")} == response
