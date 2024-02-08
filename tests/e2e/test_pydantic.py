#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
from enum import Enum
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler

import pytest
from http_test import HTTPTestServer
from meatie import ParseResponseError, endpoint
from meatie_aiohttp import AiohttpClient

pydantic = pytest.importorskip("pydantic")
BaseModel: type = pydantic.BaseModel


class ResponseV1(BaseModel):
    status: str


@pytest.mark.asyncio()
async def test_can_parse_pydantic_model(test_server: HTTPTestServer) -> None:
    # GIVEN
    def handler(request: BaseHTTPRequestHandler) -> None:
        request.send_response(HTTPStatus.OK)
        request.send_header("Content-Type", "application/json")
        request.end_headers()
        request.wfile.write('{"status": "ok"}'.encode("utf-8"))

    test_server.handler = handler

    class TestClient(AiohttpClient):
        @endpoint("/")
        async def get_response(self) -> ResponseV1:
            ...

    # WHEN
    async with TestClient(test_server.create_session()) as client:
        response = await client.get_response()

    # THEN
    assert ResponseV1(status="ok") == response


@pytest.mark.asyncio()
async def test_can_handle_corrupted_pydantic_model(test_server: HTTPTestServer) -> None:
    # GIVEN
    def handler(request: BaseHTTPRequestHandler) -> None:
        request.send_response(HTTPStatus.OK)
        request.send_header("Content-Type", "application/json")
        request.end_headers()
        request.wfile.write('{"code": "ok"}'.encode("utf-8"))

    test_server.handler = handler

    class TestClient(AiohttpClient):
        @endpoint("/")
        async def get_response(self) -> ResponseV1:
            ...

    # WHEN
    with pytest.raises(ParseResponseError) as exc_info:
        async with TestClient(test_server.create_session()) as client:
            await client.get_response()

    # THEN
    exc = exc_info.value
    assert HTTPStatus.OK == exc.response.status


class StatusCode(str, Enum):
    OK = "OK"


class ResponseV2(BaseModel):
    status: StatusCode


@pytest.mark.asyncio()
async def test_can_handle_corrupted_pydantic_model_with_enum(http_server: HTTPTestServer) -> None:
    # GIVEN
    def handler(request: BaseHTTPRequestHandler) -> None:
        request.send_response(HTTPStatus.OK)
        request.send_header("Content-Type", "application/json")
        request.end_headers()
        request.wfile.write('{"status": "ok"}'.encode("utf-8"))

    http_server.handler = handler

    class TestClient(AiohttpClient):
        @endpoint("/")
        async def get_response(self) -> ResponseV2:
            ...

    # WHEN
    with pytest.raises(ParseResponseError) as exc_info:
        async with TestClient(http_server.create_session()) as client:
            await client.get_response()

    # THEN
    exc = exc_info.value
    assert HTTPStatus.OK == exc.response.status
