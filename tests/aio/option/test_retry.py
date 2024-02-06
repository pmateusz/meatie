#  Copyright 2023 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

from http import HTTPStatus
from typing import Any, cast
from unittest.mock import AsyncMock, Mock

import pytest
from aiohttp import ClientResponseError, ClientSession
from meatie.aio import Retry, StopAfter, WaitExponential, endpoint
from meatie_aiohttp import AiohttpClient

from tests.aio.conftest import MockTools

PRODUCTS = [{"name": "headphones"}]


@pytest.mark.asyncio()
async def test_no_retry_on_success_status(mock_tools: MockTools) -> None:
    # GIVEN
    session = mock_tools.session_with_json_response(json=PRODUCTS, status=HTTPStatus.OK)

    class Store(AiohttpClient):
        def __init__(self) -> None:
            super().__init__(cast(ClientSession, session))

        @endpoint("/api/v1/products", Retry())
        async def get_products(self) -> list[Any]:
            ...

    # WHEN
    async with Store() as api:
        result = await api.get_products()

    # THEN
    assert PRODUCTS == result
    session.request.assert_awaited_once()


@pytest.mark.asyncio()
async def test_no_retry_on_bad_request(mock_tools: MockTools) -> None:
    # GIVEN
    session = mock_tools.session_with_json_client_response_error(HTTPStatus.BAD_REQUEST)

    class Store(AiohttpClient):
        def __init__(self) -> None:
            super().__init__(cast(ClientSession, session))

        @endpoint("/api/v1/products", Retry())
        async def get_products(self) -> list[Any]:
            ...

    # WHEN
    with pytest.raises(ClientResponseError):
        async with Store() as api:
            await api.get_products()

    # THEN
    session.request.assert_awaited_once()


@pytest.mark.asyncio()
async def test_can_retry(mock_tools: MockTools) -> None:
    # GIVEN
    error_response = mock_tools.json_client_response_error(HTTPStatus.TOO_MANY_REQUESTS)
    ok_response = mock_tools.json_response(json=PRODUCTS)
    session = Mock(spec=ClientSession, request=AsyncMock(side_effect=[error_response, ok_response]))

    class Store(AiohttpClient):
        def __init__(self) -> None:
            super().__init__(cast(ClientSession, session))

        @endpoint("/api/v1/products", Retry(sleep_func=AsyncMock()))
        async def get_products(self) -> list[Any]:
            ...

    # WHEN
    async with Store() as api:
        await api.get_products()

    # THEN
    ok_response.json.assert_awaited_once()


@pytest.mark.asyncio()
async def test_can_throw_rate_limit_exceeded(mock_tools: MockTools) -> None:
    # GIVEN
    response = mock_tools.json_client_response_error(HTTPStatus.TOO_MANY_REQUESTS)
    session = mock_tools.session_wrap_response(response)
    attempts = 5

    class Store(AiohttpClient):
        def __init__(self) -> None:
            super().__init__(cast(ClientSession, session))

        @endpoint(
            "/api/v1/products",
            Retry(sleep_func=AsyncMock(), wait=WaitExponential(), stop=StopAfter(attempts)),
        )
        async def get_products(self) -> list[Any]:
            ...

    # WHEN
    with pytest.raises(ClientResponseError):
        async with Store() as api:
            await api.get_products()

    # THEN
    assert response.json.await_count == attempts
