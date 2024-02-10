#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

from typing import Any, cast
from unittest.mock import patch

import pytest
from aiohttp import ClientSession
from meatie import endpoint, private
from meatie_aiohttp import Client
from mock_tools import AiohttpMockTools


@pytest.mark.asyncio()
async def test_calls_authenticate_on_private_endpoint(mock_tools: AiohttpMockTools) -> None:
    # GIVEN
    products = [{"name": "pencil"}, {"name": "headphones"}]
    session = mock_tools.session_with_json_response(json=products)

    class Store(Client):
        def __init__(self) -> None:
            super().__init__(cast(ClientSession, session))

        @endpoint("/api/v1/products", private)
        async def get_products(self) -> list[Any]:
            ...

    # WHEN
    async with Store() as api:
        with patch.object(api, "authenticate") as method_mock:
            results = await api.get_products()

    # THEN
    assert products == results
    method_mock.assert_awaited_once()
    session.request.assert_awaited_once()
