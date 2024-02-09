#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

from typing import Any, cast

import pytest
from aiohttp import ClientSession
from meatie import INF, endpoint
from meatie.aio import cache
from meatie_aiohttp import AiohttpClient

from tests.client.aiohttp_.mock_tools import MockTools

PRODUCTS = [{"name": "pencil"}, {"name": "headphones"}]


@pytest.mark.asyncio()
async def test_local_cache_is_isolated(mock_tools: MockTools) -> None:
    # GIVEN
    session = mock_tools.session_with_json_response(json=PRODUCTS)

    class Store(AiohttpClient):
        def __init__(self) -> None:
            super().__init__(cast(ClientSession, session))

        @endpoint("/api/v1/products", cache(ttl=INF, shared=False))
        async def get_products(self) -> list[Any]:
            ...

    # WHEN
    async with Store() as api:
        first_result = await api.get_products()

    # THEN
    assert PRODUCTS == first_result
    session.request.assert_awaited_once()

    # WHEN
    session.request.reset_mock()
    async with Store() as api:
        second_result = await api.get_products()

    # THEN
    assert PRODUCTS == second_result
    session.request.assert_awaited_once()


@pytest.mark.asyncio()
async def test_global_cache_is_shared(mock_tools: MockTools) -> None:
    # GIVEN
    session = mock_tools.session_with_json_response(json=PRODUCTS)

    class Store(AiohttpClient):
        def __init__(self) -> None:
            super().__init__(session)

        @endpoint("/api/v1/products", cache(ttl=INF, shared=True))
        async def get_products(self) -> list[Any]:
            ...

    # WHEN
    async with Store() as api:
        first_result = await api.get_products()

    # THEN
    assert PRODUCTS == first_result
    session.request.assert_awaited_once()

    # WHEN
    session.request.reset_mock()
    async with Store() as api:
        second_result = await api.get_products()

    # THEN
    assert PRODUCTS == second_result
    session.request.assert_not_called()
