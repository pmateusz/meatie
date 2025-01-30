#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
from typing import Optional

import pytest
from aiohttp import ClientSession
from http_test import HTTPTestServer
from http_test.handlers import service_unavailable
from meatie import AsyncResponse, HttpStatusError, ResponseError, body, endpoint
from meatie_aiohttp import Client


async def get_error(response: AsyncResponse) -> Optional[Exception]:
    if response.status < 400:
        return None

    exc_type = HttpStatusError if response.status >= 300 else ResponseError
    return exc_type(response)


@pytest.mark.asyncio()
async def test_raises_error(http_server: HTTPTestServer) -> None:
    # GIVEN
    http_server.handler = service_unavailable

    class TestClient(Client):
        @endpoint("/", body(error=get_error))
        async def get_response(self) -> dict[str, str]:
            ...

    # WHEN
    async with TestClient(ClientSession(http_server.base_url)) as client:
        with pytest.raises(HttpStatusError) as exc_info:
            await client.get_response()

        # THEN
        response = await exc_info.value.response.json()
        assert response == {"error": "deployment in progress"}
