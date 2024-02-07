#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
import asyncio
import contextlib
import time
from asyncio import AbstractEventLoop
from http import HTTPStatus
from json import JSONDecodeError
from typing import Generator, Any, Callable

import aiohttp
import httpx
import pytest
import requests
from http_test import (
    ClientAdapter,
    Handler,
    HTTPSTestServer,
    HTTPTestServer,
    StatusHandler,
    diagnostic_handler,
    echo_handler,
)
from meatie import (
    Client,
    ParseResponseError,
    ProxyError,
    Request,
    RequestError,
    ServerError,
    Timeout,
    TransportError,
)
from meatie_aiohttp import AiohttpClient
from meatie_httpx import HttpxClient
from meatie_requests.client import RequestsClient


class DefaultSuite:
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
        assert exc.response is not None
        assert "{invalid-json}" == exc.text
        assert HTTPStatus.OK == exc.response.status
        assert isinstance(exc.cause, JSONDecodeError)

    @staticmethod
    def test_can_handle_connection_reset(test_server: HTTPTestServer, client: Client) -> None:
        def connection_reset_handler(handler: Handler) -> None:
            handler.wfile.close()

        test_server.handler = connection_reset_handler
        request = Request("GET", test_server.base_url, query_params={}, headers={})

        # WHEN
        with pytest.raises(ServerError) as exc_info:
            client.send(request)

        # THEN
        assert exc_info.value.cause is not None

    @staticmethod
    def test_rejects_untrusted_cert(test_tls_server: HTTPSTestServer, client: Client) -> None:
        # GIVEN
        test_tls_server.handler = StatusHandler(HTTPStatus.OK)
        request = Request("GET", test_tls_server.base_url, query_params={}, headers={})

        # WHEN
        with pytest.raises(ServerError) as exc_info:
            client.send(request)

        # THEN
        assert exc_info.value.cause is not None

    @staticmethod
    def test_rejects_http_protocol_when_https_is_requested(
        client: Client, test_server: HTTPTestServer
    ) -> None:
        # GIVEN
        request = Request(
            "GET", f"https://localhost:{test_server.port}", query_params={}, headers={}
        )

        # WHEN
        with pytest.raises(ServerError) as exc_info:
            client.send(request)

        # THEN
        assert exc_info.value.cause is not None

    @staticmethod
    def test_can_handle_connection_error(client: Client) -> None:
        # GIVEN
        request = Request("GET", "http://localhost:1234", query_params={}, headers={})

        # WHEN
        with pytest.raises(ServerError) as exc_info:
            client.send(request)

        # THEN
        assert exc_info.value.cause is not None

    @staticmethod
    def test_can_handle_schema_error(client: Client, test_server: HTTPTestServer) -> None:
        # GIVEN
        request = Request(
            "GET", f"unknown://localhost:{test_server.port}", query_params={}, headers={}
        )

        # WHEN
        with pytest.raises(RequestError) as exc_info:
            client.send(request)

        # THEN
        assert exc_info.value.cause is not None


class TimeoutSuite:
    @staticmethod
    def test_can_handle_timeout(test_server: HTTPTestServer, client: Client) -> None:
        # GIVEN
        def timeout_handler(handler: Handler) -> None:
            time.sleep(0.01)
            handler.send_response(HTTPStatus.OK)

        test_server.handler = timeout_handler
        request = Request("GET", test_server.base_url, query_params={}, headers={})

        # WHEN
        with pytest.raises(Timeout) as exc_info:
            client.send(request)

        # THEN
        assert exc_info.value.cause is not None


class ProxyErrorSuite:
    @staticmethod
    def test_can_handle_proxy_error(client: Client, test_server: HTTPTestServer) -> None:
        # GIVEN
        request = Request("GET", test_server.base_url, query_params={}, headers={})

        # WHEN
        with pytest.raises(ProxyError) as exc_info:
            client.send(request)

        # THEN
        assert exc_info.value.cause is not None


class TestRequestsDefaultSuite(DefaultSuite):
    @pytest.fixture(name="client")
    def client_fixture(self) -> Generator[RequestsClient, None, None]:
        with RequestsClient(requests.Session()) as client:
            yield client


class TestRequestsTimeoutSuite(TimeoutSuite):
    @pytest.fixture(name="client")
    def client_fixture(self) -> Generator[RequestsClient, None, None]:
        with RequestsClient(requests.Session(), session_params={"timeout": 0.005}) as client:
            yield client


class TestRequestsProxyErrorSuite(ProxyErrorSuite):
    @pytest.fixture(name="client")
    def client_fixture(self) -> Generator[RequestsClient, None, None]:
        with RequestsClient(
            requests.Session(),
            session_params={
                "proxies": {
                    "http": "http://localhost:3128",
                }
            },
        ) as client:
            yield client


class TestHttpxDefaultSuite(DefaultSuite):
    @pytest.fixture(name="client")
    def client_fixture(self) -> Generator[HttpxClient, None, None]:
        with HttpxClient(httpx.Client()) as client:
            yield client


class TestHttpxTimeoutSuite(TimeoutSuite):
    @pytest.fixture(name="client")
    def client_fixture(self) -> Generator[HttpxClient, None, None]:
        with HttpxClient(httpx.Client(), session_params={"timeout": 0.005}) as client:
            yield client


class TestHttpxProxyErrorSuite:
    @pytest.fixture(name="client")
    def client_fixture(self) -> Generator[HttpxClient, None, None]:
        with HttpxClient(httpx.Client(proxy="http://localhost:3128")) as client:
            yield client

    @staticmethod
    def test_can_handle_proxy_error(client: Client, test_server: HTTPTestServer) -> None:
        # GIVEN
        request = Request("GET", test_server.base_url, query_params={}, headers={})

        # WHEN
        with pytest.raises(ServerError) as exc_info:
            client.send(request)

        # THEN
        assert exc_info.value.cause is not None


async def _create_client_session(*args: Any, **kwargs: Any) -> aiohttp.ClientSession:
    return aiohttp.ClientSession(*args, **kwargs)


@pytest.fixture(name="create_client_session")
def create_client_session_fixture(event_loop: AbstractEventLoop) -> Callable[..., aiohttp.ClientSession]:
    def create_client_session(*args: Any, **kwargs: Any) -> aiohttp.ClientSession:
        return event_loop.run_until_complete(_create_client_session(*args, **kwargs))

    return create_client_session


class TestAiohttpDefaultSuite(DefaultSuite):
    @pytest.fixture(name="client")
    def client_fixture(self, event_loop: asyncio.AbstractEventLoop, create_client_session) -> Generator[
        ClientAdapter, None, None]:
        with ClientAdapter(event_loop, AiohttpClient(create_client_session())) as client:
            yield client

    @staticmethod
    def test_can_handle_schema_error(client: Client, test_server: HTTPTestServer) -> None:
        # GIVEN
        test_server.handler = StatusHandler(HTTPStatus.OK)
        request = Request(
            "GET", f"unknown://localhost:{test_server.port}", query_params={}, headers={}
        )

        # WHEN
        response = client.send(request)

        # THEN
        assert HTTPStatus.OK == response.status


class TestAiohttpTimeoutSuite(TimeoutSuite):
    @pytest.fixture(name="client")
    def client_fixture(self, event_loop: asyncio.AbstractEventLoop, create_client_session) -> Generator[
        ClientAdapter, None, None]:
        with ClientAdapter(
            event_loop,
            AiohttpClient(create_client_session(timeout=aiohttp.ClientTimeout(total=0.005))),
        ) as client:
            yield client


class TestAiohttpProxyErrorSuite(ProxyErrorSuite):

    @pytest.fixture(name="client")
    def client_fixture(self, event_loop: asyncio.AbstractEventLoop, create_client_session) -> Generator[
        ClientAdapter, None, None]:
        with ClientAdapter(
            event_loop,
            AiohttpClient(
                create_client_session(), session_params={"proxy": "http://localhost:3128"}
            ),
        ) as client:
            yield client


class RaiseForStatusSuite:
    @staticmethod
    def test_can_handle_proxy_error(client: Client, test_server: HTTPTestServer) -> None:
        # GIVEN
        test_server.handler = StatusHandler(HTTPStatus.BAD_REQUEST)
        request = Request("GET", test_server.base_url, query_params={}, headers={})

        # WHEN
        with pytest.raises(TransportError) as exc_info:
            client.send(request)

        # THEN
        assert exc_info.value.cause is not None

# TODO:
# - can handle raise for status, figure our useful exceptions for retries
