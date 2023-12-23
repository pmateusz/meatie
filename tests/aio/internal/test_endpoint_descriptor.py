#  Copyright 2023 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

from typing import Any

import pytest
from meatie.aio import Client, endpoint

from tests.aio.conftest import MockTools

PRODUCTS = [{"name": "Pencil"}, {"name": "Headphones"}]


@pytest.mark.asyncio()
async def test_get_without_parameters(mock_tools: MockTools) -> None:
    # GIVEN
    session = mock_tools.session_with_json_response(json=PRODUCTS)

    class Store(Client):
        def __init__(self) -> None:
            super().__init__(session)

        @endpoint("/api/v1/products")
        async def get_products(self) -> list[Any]:
            ...

    # WHEN
    async with Store() as api:
        result = await api.get_products()

    # THEN
    assert PRODUCTS == result
    session.request.assert_awaited_once_with("GET", "/api/v1/products")


@pytest.mark.asyncio()
async def test_post_with_body(mock_tools: MockTools) -> None:
    # GIVEN
    session = mock_tools.session_with_json_response(json=None)

    class Store(Client):
        def __init__(self) -> None:
            super().__init__(session)

        @endpoint("/api/v1/order")
        async def post_order(self, body: Any) -> None:
            ...

    # WHEN
    async with Store() as api:
        await api.post_order(PRODUCTS)

    # THEN
    session.request.assert_awaited_once_with("POST", "/api/v1/order", json=PRODUCTS)
