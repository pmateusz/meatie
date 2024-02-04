#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

from http import HTTPStatus
from typing import Generator

import httpx
import pytest
import requests
from http_test import HTTPTestServer, status_handler
from meatie.internal.types import Client, Request
from meatie_httpx import HttpxClient
from meatie_requests.client import RequestsClient


class ClientTestSuite:
    def test_can_send_get_request(self, test_server: HTTPTestServer, client: Client) -> None:
        # GIVEN
        test_server.handler = status_handler(HTTPStatus.OK)
        request = Request("GET", test_server.base_url, query_params={}, headers={})

        # WHEN
        response = client.send(request)

        # THEN
        assert HTTPStatus.OK == response.status


# TODO:
#  - test can read binary body (ok, malformed response)
#  - can read text (ok, malformed encoding),
#  - can read json (ok, malformed json),
#  - can handle handle status codes 5XX, 4XX
#  - can handle timeouts
#  - can handle connection reset


class TestRequestsClient(ClientTestSuite):
    @pytest.fixture(name="client")
    def client_fixture(self) -> Generator[RequestsClient, None, None]:
        with RequestsClient(requests.Session()) as client:
            yield client


class TestHttpxClient(ClientTestSuite):
    @pytest.fixture(name="client")
    def client_fixture(self) -> Generator[HttpxClient, None, None]:
        with HttpxClient(httpx.Client()) as client:
            yield client
