#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

from http import HTTPStatus
from json import JSONDecodeError
from typing import Generator

import httpx
import pytest
import requests
from http_test import (
    Handler,
    HTTPTestServer,
    StatusHandler,
    diagnostic_handler,
    echo_handler,
)
from meatie.aio import ParseResponseError
from meatie.internal.error import TransportError
from meatie.internal.types import Client, Request
from meatie_httpx import HttpxClient
from meatie_requests.client import RequestsClient


class ClientTestSuite:
    @staticmethod
    def test_can_send_get_request(test_server: HTTPTestServer, client: Client) -> None:
        # GIVEN
        test_server.handler = StatusHandler(HTTPStatus.OK)
        request = Request("GET", test_server.base_url, query_params={}, headers={})

        # WHEN
        response = client.send(request)

        # THEN
        assert HTTPStatus.OK == response.status

    @staticmethod
    def test_can_send_query_params(test_server: HTTPTestServer, client: Client) -> None:
        # GIVEN
        test_server.handler = diagnostic_handler
        request = Request("GET", test_server.base_url, query_params={"param": 123}, headers={})

        # WHEN
        response = client.send(request)

        # THEN
        assert HTTPStatus.OK == response.status
        content = response.json()
        assert isinstance(content, dict)
        assert "param=123" == content.get("query")

    @staticmethod
    def test_can_send_headers(test_server: HTTPTestServer, client: Client) -> None:
        # GIVEN
        test_server.handler = diagnostic_handler
        request = Request("GET", test_server.base_url, query_params={}, headers={"x-header": "123"})

        # WHEN
        response = client.send(request)

        # THEN
        assert HTTPStatus.OK == response.status
        content = response.json()
        assert isinstance(content, dict)
        headers = content.get("headers", {})
        assert "123" == headers.get("x-header")

    @staticmethod
    def test_can_send_post_binary_request(test_server: HTTPTestServer, client: Client) -> None:
        # GIVEN
        test_server.handler = echo_handler
        request = Request("POST", test_server.base_url, query_params={}, headers={}, data=b"body")

        # WHEN
        response = client.send(request)

        # THEN
        assert HTTPStatus.OK == response.status
        assert b"body" == response.read()

    @staticmethod
    def test_can_send_post_text_request(test_server: HTTPTestServer, client: Client) -> None:
        # GIVEN
        test_server.handler = echo_handler
        request = Request("POST", test_server.base_url, query_params={}, headers={}, data="body")

        # WHEN
        response = client.send(request)

        # THEN
        assert HTTPStatus.OK == response.status
        assert "body" == response.text()

    @staticmethod
    def test_can_send_post_json_request(test_server: HTTPTestServer, client: Client) -> None:
        # GIVEN
        test_server.handler = echo_handler
        request = Request(
            "POST", test_server.base_url, query_params={}, headers={}, json={"key": "123"}
        )

        # WHEN
        response = client.send(request)

        # THEN
        assert HTTPStatus.OK == response.status
        assert {"key": "123"} == response.json()

    @staticmethod
    def test_can_receive_4xx_status(test_server: HTTPTestServer, client: Client) -> None:
        # GIVEN
        test_server.handler = StatusHandler(HTTPStatus.BAD_REQUEST)
        request = Request("GET", test_server.base_url, query_params={}, headers={})

        # WHEN
        response = client.send(request)

        # THEN
        assert HTTPStatus.BAD_REQUEST == response.status

    @staticmethod
    def test_can_receive_5xx_status(test_server: HTTPTestServer, client: Client) -> None:
        # GIVEN
        test_server.handler = StatusHandler(HTTPStatus.INTERNAL_SERVER_ERROR)
        request = Request("GET", test_server.base_url, query_params={}, headers={})

        # WHEN
        response = client.send(request)

        # THEN
        assert HTTPStatus.INTERNAL_SERVER_ERROR == response.status

    @staticmethod
    def test_can_handle_malformed_text_encoding(
        test_server: HTTPTestServer, client: Client
    ) -> None:
        # GIVEN
        def malformed_text_handler(handler: Handler) -> None:
            handler.send_bytes(
                HTTPStatus.OK, "text/plain; charset=ascii", bytes([0xF0, 0x9F, 0x9A, 0x80])
            )

        test_server.handler = malformed_text_handler
        request = Request("GET", test_server.base_url, query_params={}, headers={})

        # WHEN
        response = client.send(request)

        # THEN
        assert HTTPStatus.OK == response.status
        text = response.text()
        assert "����" == text

    @staticmethod
    def test_can_handle_malformed_json(test_server: HTTPTestServer, client: Client) -> None:
        # GIVEN
        def malformed_text_handler(handler: Handler) -> None:
            handler.send_bytes(
                HTTPStatus.OK, "application/json; charset=utf-8", "{invalid-json}".encode("utf-8")
            )

        test_server.handler = malformed_text_handler
        request = Request("GET", test_server.base_url, query_params={}, headers={})

        # WHEN
        response = client.send(request)
        with pytest.raises(ParseResponseError) as exc_info:
            response.json()

        # THEN
        exc = exc_info.value
        assert exc.response is response
        assert isinstance(exc.cause, JSONDecodeError)
        assert HTTPStatus.OK == exc.response.status

    @staticmethod
    def test_can_handle_connection_reset(test_server: HTTPTestServer, client: Client) -> None:
        def connection_reset_handler(handler: Handler) -> None:
            handler.wfile.close()

        test_server.handler = connection_reset_handler
        request = Request("GET", test_server.base_url, query_params={}, headers={})

        # WHEN
        with pytest.raises(TransportError) as exc_info:
            client.send(request)

        # THEN
        assert exc_info.value.cause is not None


# TODO:
# - can handle timeouts
# - can handle raise for status
# - can handle tls errors
# - async to sync adapter


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
