#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

from http import HTTPStatus
from typing import AsyncGenerator

import aiohttp
import pytest
import pytest_asyncio
from http_test import HTTPTestServer, status_handler
from meatie.internal.types import Request
from meatie_aiohttp import AiohttpClient


class AsyncClientTestSuite:
    @pytest.mark.asyncio()
    async def test_can_send_get_request(
        self, test_server: HTTPTestServer, async_client: AiohttpClient
    ) -> None:
        # GIVEN
        test_server.handler = status_handler(HTTPStatus.OK)
        request = Request("GET", test_server.base_url, query_params={}, headers={})

        # WHEN
        response = await async_client.send(request)

        # THEN
        assert HTTPStatus.OK == response.status


class TestAiohttp(AsyncClientTestSuite):
    @pytest_asyncio.fixture(name="async_client")
    async def client_fixture(self) -> AsyncGenerator[AiohttpClient, None]:
        async with AiohttpClient(aiohttp.ClientSession()) as client:
            yield client
