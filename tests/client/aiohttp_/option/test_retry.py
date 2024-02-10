#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

from http import HTTPStatus
from typing import Any
from unittest.mock import AsyncMock, Mock

import pytest
from aiohttp import ClientSession
from meatie import ResponseError, after_attempt, endpoint, exponential, retry
from meatie_aiohttp import AiohttpClient
from mock_tools import AiohttpMockTools

PRODUCTS = [{"name": "headphones"}]


@pytest.mark.asyncio()
async def test_no_retry_on_success_status(mock_tools: AiohttpMockTools) -> None:
    # GIVEN
    session = mock_tools.session_with_json_response(json=PRODUCTS, status=HTTPStatus.OK)

    class Store(AiohttpClient):
        def __init__(self) -> None:
            super().__init__(session)

        @endpoint("/api/v1/products", retry())
        async def get_products(self) -> list[Any]:
            ...

    # WHEN
    async with Store() as api:
        result = await api.get_products()

    # THEN
    assert PRODUCTS == result
    session.request.assert_awaited_once()


@pytest.mark.asyncio()
async def test_no_retry_on_bad_request(mock_tools: AiohttpMockTools) -> None:
    # GIVEN
    session = mock_tools.session_with_json_client_response_error(HTTPStatus.BAD_REQUEST)

    class Store(AiohttpClient):
        def __init__(self) -> None:
            super().__init__(session)

        @endpoint("/api/v1/products", retry())
        async def get_products(self) -> list[Any]:
            ...

    # WHEN
    with pytest.raises(ResponseError):
        async with Store() as api:
            await api.get_products()

    # THEN
    session.request.assert_awaited_once()


@pytest.mark.asyncio()
async def test_can_retry(mock_tools: AiohttpMockTools) -> None:
    # GIVEN
    error_response = mock_tools.json_client_response_error(HTTPStatus.TOO_MANY_REQUESTS)
    ok_response = mock_tools.json_response(json=PRODUCTS)
    session = Mock(spec=ClientSession, request=AsyncMock(side_effect=[error_response, ok_response]))

    class Store(AiohttpClient):
        def __init__(self) -> None:
            super().__init__(session)

        @endpoint("/api/v1/products", retry(sleep_func=AsyncMock()))
        async def get_products(self) -> list[Any]:
            ...

    # WHEN
    async with Store() as api:
        await api.get_products()

    # THEN
    ok_response.json.assert_awaited_once()


@pytest.mark.asyncio()
async def test_can_throw_rate_limit_exceeded(mock_tools: AiohttpMockTools) -> None:
    # GIVEN
    response = mock_tools.json_client_response_error(HTTPStatus.TOO_MANY_REQUESTS)
    session = mock_tools.session_wrap_response(response)
    attempts = 5
    sleep_func = AsyncMock()

    class Store(AiohttpClient):
        def __init__(self) -> None:
            super().__init__(session)

        @endpoint(
            "/api/v1/products",
            retry(sleep_func=sleep_func, wait=exponential(), stop=after_attempt(attempts)),
        )
        async def get_products(self) -> list[Any]:
            ...

    # WHEN
    with pytest.raises(ResponseError):
        async with Store() as api:
            await api.get_products()

    # THEN
    assert sleep_func.await_count == attempts - 1
    assert response.json.await_count == attempts
