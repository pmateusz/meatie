#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.


from typing import Generator

import httpx
import pytest
from http_test import HTTPTestServer
from meatie import Request, ServerError
from meatie.types import Client
from meatie_httpx import HttpxClient


class TestHttpxProxyErrorSuite:
    @pytest.fixture(name="client")
    def client_fixture(self) -> Generator[HttpxClient, None, None]:
        with HttpxClient(httpx.Client(proxy="http://localhost:3128")) as client:
            yield client

    @staticmethod
    def test_can_handle_proxy_error(client: Client, http_server: HTTPTestServer) -> None:
        # GIVEN
        request = Request("GET", http_server.base_url, query_params={}, headers={})

        # WHEN
        with pytest.raises(ServerError) as exc_info:
            client.send(request)

        # THEN
        assert exc_info.value.cause is not None
