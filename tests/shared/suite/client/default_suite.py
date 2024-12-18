#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
from http import HTTPStatus
from json import JSONDecodeError

import pytest
from http_test import (
    HTTPSTestServer,
    HTTPTestServer,
)
from http_test.handlers import Handler, diagnostic_handler, echo_handler, StatusHandler
from meatie import (
    ParseResponseError,
    Request,
    RequestError,
    ServerError,
)
from meatie.internal.types import Client


class DefaultSuite:
    @staticmethod
    def test_can_send_get_request(http_server: HTTPTestServer, client: Client) -> None:
        # GIVEN
        http_server.handler = StatusHandler(HTTPStatus.OK)
        request = Request("GET", http_server.base_url, params={}, headers={})

        # WHEN
        response = client.send(request)

        # THEN
        assert HTTPStatus.OK == response.status

    @staticmethod
    def test_can_send_query_params(http_server: HTTPTestServer, client: Client) -> None:
        # GIVEN
        http_server.handler = diagnostic_handler
        request = Request("GET", http_server.base_url, params={"param": 123}, headers={})

        # WHEN
        response = client.send(request)

        # THEN
        assert HTTPStatus.OK == response.status
        content = response.json()
        assert isinstance(content, dict)
        assert "param=123" == content.get("query")

    @staticmethod
    def test_can_send_headers(http_server: HTTPTestServer, client: Client) -> None:
        # GIVEN
        http_server.handler = diagnostic_handler
        request = Request("GET", http_server.base_url, params={}, headers={"x-header": "123"})

        # WHEN
        response = client.send(request)

        # THEN
        assert HTTPStatus.OK == response.status
        content = response.json()
        assert isinstance(content, dict)
        headers = content.get("headers", {})
        assert "123" == headers.get("x-header")

    @staticmethod
    def test_can_send_post_binary_request(http_server: HTTPTestServer, client: Client) -> None:
        # GIVEN
        http_server.handler = echo_handler
        request = Request("POST", http_server.base_url, params={}, headers={}, data=b"body")

        # WHEN
        response = client.send(request)

        # THEN
        assert HTTPStatus.OK == response.status
        assert b"body" == response.read()

    @staticmethod
    def test_can_send_post_text_request(http_server: HTTPTestServer, client: Client) -> None:
        # GIVEN
        http_server.handler = echo_handler
        request = Request("POST", http_server.base_url, params={}, headers={}, data="body")

        # WHEN
        response = client.send(request)

        # THEN
        assert HTTPStatus.OK == response.status
        assert "body" == response.text()

    @staticmethod
    def test_can_send_post_json_request(http_server: HTTPTestServer, client: Client) -> None:
        # GIVEN
        http_server.handler = echo_handler
        request = Request("POST", http_server.base_url, params={}, headers={}, json={"key": "123"})

        # WHEN
        response = client.send(request)

        # THEN
        assert HTTPStatus.OK == response.status
        assert {"key": "123"} == response.json()

    @staticmethod
    def test_can_receive_4xx_status(http_server: HTTPTestServer, client: Client) -> None:
        # GIVEN
        http_server.handler = StatusHandler(HTTPStatus.BAD_REQUEST)
        request = Request("GET", http_server.base_url, params={}, headers={})

        # WHEN
        response = client.send(request)

        # THEN
        assert HTTPStatus.BAD_REQUEST == response.status

    @staticmethod
    def test_can_receive_5xx_status(http_server: HTTPTestServer, client: Client) -> None:
        # GIVEN
        http_server.handler = StatusHandler(HTTPStatus.INTERNAL_SERVER_ERROR)
        request = Request("GET", http_server.base_url, params={}, headers={})

        # WHEN
        response = client.send(request)

        # THEN
        assert HTTPStatus.INTERNAL_SERVER_ERROR == response.status

    @staticmethod
    def test_can_handle_malformed_text_encoding(
        http_server: HTTPTestServer, client: Client
    ) -> None:
        # GIVEN
        def malformed_text_handler(handler: Handler) -> None:
            handler.send_bytes(
                HTTPStatus.OK, "text/plain; charset=ascii", bytes([0xF0, 0x9F, 0x9A, 0x80])
            )

        http_server.handler = malformed_text_handler
        request = Request("GET", http_server.base_url, params={}, headers={})

        # WHEN
        response = client.send(request)

        # THEN
        assert HTTPStatus.OK == response.status
        text = response.text()
        assert "����" == text

    @staticmethod
    def test_can_handle_malformed_json(http_server: HTTPTestServer, client: Client) -> None:
        # GIVEN
        def malformed_text_handler(handler: Handler) -> None:
            handler.send_bytes(
                HTTPStatus.OK, "application/json; charset=utf-8", "{invalid-json}".encode("utf-8")
            )

        http_server.handler = malformed_text_handler
        request = Request("GET", http_server.base_url, params={}, headers={})

        # WHEN
        response = client.send(request)
        with pytest.raises(ParseResponseError) as exc_info:
            response.json()

        # THEN
        exc = exc_info.value
        assert exc.response is not None
        assert "{invalid-json}" == exc.text
        assert HTTPStatus.OK == exc.response.status
        assert isinstance(exc.__cause__, JSONDecodeError)

    @staticmethod
    def test_can_handle_connection_reset(http_server: HTTPTestServer, client: Client) -> None:
        def connection_reset_handler(handler: Handler) -> None:
            handler.wfile.close()

        http_server.handler = connection_reset_handler
        request = Request("GET", http_server.base_url, params={}, headers={})

        # WHEN
        with pytest.raises(ServerError) as exc_info:
            client.send(request)

        # THEN
        assert exc_info.value.__cause__ is not None

    @staticmethod
    def test_rejects_untrusted_cert(
        untrusted_https_server: HTTPSTestServer, client: Client
    ) -> None:
        # GIVEN
        untrusted_https_server.handler = StatusHandler(HTTPStatus.OK)
        request = Request("GET", untrusted_https_server.base_url, params={}, headers={})

        # WHEN
        with pytest.raises(ServerError) as exc_info:
            client.send(request)

        # THEN
        assert exc_info.value.__cause__ is not None

    @staticmethod
    def test_rejects_http_protocol_when_https_is_requested(
        http_server: HTTPTestServer, client: Client
    ) -> None:
        # GIVEN
        request = Request("GET", f"https://localhost:{http_server.port}", params={}, headers={})

        # WHEN
        with pytest.raises(ServerError) as exc_info:
            client.send(request)

        # THEN
        assert exc_info.value.__cause__ is not None

    @staticmethod
    def test_can_handle_connection_error(client: Client) -> None:
        # GIVEN
        request = Request("GET", "http://localhost:1234", params={}, headers={})

        # WHEN
        with pytest.raises(ServerError) as exc_info:
            client.send(request)

        # THEN
        assert exc_info.value.__cause__ is not None

    @staticmethod
    def test_can_handle_schema_error(http_server: HTTPTestServer, client: Client) -> None:
        # GIVEN
        request = Request("GET", f"unknown://localhost:{http_server.port}", params={}, headers={})

        # WHEN
        with pytest.raises(RequestError) as exc_info:
            client.send(request)

        # THEN
        assert exc_info.value.__cause__ is not None
