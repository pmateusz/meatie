#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
import asyncio
from http import HTTPStatus
from typing import Generator, Callable

import aiohttp

from http_test import StatusHandler, HTTPTestServer, ClientAdapter
from meatie import Request
from meatie_aiohttp import AiohttpClient
from tests.client.default_suite import DefaultSuite
import pytest


class TestAiohttpDefaultSuite(DefaultSuite):
    @pytest.fixture(name="client")
    def client_fixture(
        self,
        event_loop: asyncio.AbstractEventLoop,
        create_client_session: Callable[..., aiohttp.ClientSession],
    ) -> Generator[ClientAdapter, None, None]:
        with ClientAdapter(event_loop, AiohttpClient(create_client_session())) as client:
            yield client

    @staticmethod
    def test_can_handle_schema_error(client: ClientAdapter, http_server: HTTPTestServer) -> None:
        # GIVEN
        http_server.handler = StatusHandler(HTTPStatus.OK)
        request = Request(
            "GET", f"unknown://localhost:{http_server.port}", query_params={}, headers={}
        )

        # WHEN
        response = client.send(request)

        # THEN
        assert HTTPStatus.OK == response.status
