#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

from typing import Any, cast
from unittest.mock import AsyncMock, patch

import pytest
from aiohttp import ClientSession
from meatie import Limiter, Rate, endpoint, limit
from meatie_aiohttp import AiohttpClient

from tests.client.aiohttp_.mock_tools import MockTools


@pytest.mark.asyncio()
async def test_waits_until_tokens_are_available(mock_tools: MockTools) -> None:
    # GIVEN
    products = [{"name": "bicycle"}]
    response = mock_tools.json_response(json=products)
    session = mock_tools.session_wrap_response(response)
    sleep_func = AsyncMock()
    current_time = 100

    with patch("time.monotonic") as time_monotonic:
        time_monotonic.return_value = current_time

        class Store(AiohttpClient):
            def __init__(self) -> None:
                super().__init__(
                    cast(ClientSession, session),
                    limiter=Limiter(Rate(1), capacity=2, init_tokens=0, init_time=current_time),
                )

            @endpoint("/api/v1/products", limit(sleep_func=sleep_func, tokens=2))
            async def get_products(self) -> list[Any]:
                ...

        # WHEN
        async with Store() as api:
            result = await api.get_products()

    # THEN
    assert products == result
    sleep_func.assert_awaited_once_with(2)
    response.json.assert_awaited_once()
