#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
import json
from decimal import Decimal
from functools import partial
from http import HTTPStatus

import pytest
from aiohttp import ClientResponse, ClientSession
from http_test import HTTPTestServer
from http_test.handlers import (
    NGINX_GATEWAY_TIMEOUT,
    magic_number,
    nginx_gateway_timeout,
    status_ok,
    status_ok_as_text,
    truncated_json,
)

from meatie import ParseResponseError, body, endpoint
from meatie_aiohttp import Client


@pytest.mark.asyncio()
async def test_can_parse_json(http_server: HTTPTestServer) -> None:
    # GIVEN
    http_server.handler = status_ok

    class TestClient(Client):
        @endpoint("/")
        async def get_response(self) -> dict[str, str]: ...

    # WHEN
    async with TestClient(ClientSession(http_server.base_url)) as client:
        response = await client.get_response()

    # THEN
    assert {"status": "ok"} == response


@pytest.mark.asyncio()
async def test_can_handle_invalid_content_type(http_server: HTTPTestServer) -> None:
    # GIVEN
    http_server.handler = status_ok_as_text

    class TestClient(Client):
        @endpoint("/")
        async def get_response(self) -> dict[str, str]: ...

    # WHEN
    with pytest.raises(ParseResponseError) as exc_info:
        async with TestClient(ClientSession(http_server.base_url)) as client:
            await client.get_response()

    # THEN
    exc = exc_info.value
    assert "{'status': 'ok'}" == exc.text
    assert HTTPStatus.OK == exc.response.status


@pytest.mark.asyncio()
async def test_can_handle_html_response(http_server: HTTPTestServer) -> None:
    # GIVEN
    http_server.handler = nginx_gateway_timeout

    class TestClient(Client):
        @endpoint("/")
        async def get_response(self) -> dict[str, str]: ...

    # WHEN
    with pytest.raises(ParseResponseError) as exc_info:
        async with TestClient(ClientSession(http_server.base_url)) as client:
            await client.get_response()

    # THEN
    exc = exc_info.value
    assert NGINX_GATEWAY_TIMEOUT == exc.text
    assert HTTPStatus.GATEWAY_TIMEOUT == exc.response.status


@pytest.mark.asyncio()
async def test_can_handle_corrupted_json(http_server: HTTPTestServer) -> None:
    # GIVEN
    http_server.handler = truncated_json

    class TestClient(Client):
        @endpoint("/")
        async def get_response(self) -> dict[str, str]: ...

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
    http_server.handler = magic_number

    async def custom_json(response: ClientResponse) -> dict[str, Decimal]:
        return await response.json(loads=partial(json.loads, parse_float=Decimal))

    class TestClient(Client):
        @endpoint("/", body(json=custom_json))
        async def get_response(self) -> dict[str, Decimal]: ...

    # WHEN
    async with TestClient(ClientSession(http_server.base_url)) as client:
        response = await client.get_response()

    # THEN
    assert {"number": Decimal("42.000000000000001")} == response
