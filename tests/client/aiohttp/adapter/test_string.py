#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

import pytest
from aiohttp import ClientSession
from http_test import HTTPTestServer
from http_test.handlers import ascii_emoji, emoji

from meatie import endpoint
from meatie_aiohttp import Client


@pytest.mark.asyncio()
async def test_can_parse_string(http_server: HTTPTestServer) -> None:
    # GIVEN
    http_server.handler = emoji

    class TestClient(Client):
        @endpoint("/")
        async def get_response(self) -> str: ...

    # WHEN
    async with TestClient(ClientSession(http_server.base_url)) as client:
        response = await client.get_response()

    # THEN
    assert "🚀" == response


@pytest.mark.asyncio()
async def test_can_handle_invalid_encoding(http_server: HTTPTestServer) -> None:
    # GIVEN
    http_server.handler = ascii_emoji

    class TestClient(Client):
        @endpoint("/")
        async def get_response(self) -> str: ...

    # WHEN
    async with TestClient(ClientSession(http_server.base_url)) as client:
        response = await client.get_response()

    # THEN
    assert "����" == response
