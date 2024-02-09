#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

from typing import Any

from meatie import INF, cache, endpoint
from meatie_httpx import HttpxClient

from tests.client.httpx_.mock_tools import MockTools

PRODUCTS = [{"name": "pencil"}, {"name": "headphones"}]


def test_local_cache_is_isolated(mock_tools: MockTools) -> None:
    # GIVEN
    client = mock_tools.client_with_json_response(json=PRODUCTS)

    class Store(HttpxClient):
        def __init__(self) -> None:
            super().__init__(client)

        @endpoint("/api/v1/products", cache(ttl=INF, shared=False))
        def get_products(self) -> list[Any]:
            ...

    # WHEN
    with Store() as api:
        first_result = api.get_products()

    # THEN
    assert PRODUCTS == first_result
    client.request.assert_called_once()

    # WHEN
    client.request.reset_mock()
    with Store() as api:
        second_result = api.get_products()

    # THEN
    assert PRODUCTS == second_result
    client.request.assert_called_once()


def test_global_cache_is_shared(mock_tools: MockTools) -> None:
    # GIVEN
    client = mock_tools.client_with_json_response(json=PRODUCTS)

    class Store(HttpxClient):
        def __init__(self) -> None:
            super().__init__(client)

        @endpoint("/api/v1/products", cache(ttl=INF, shared=True))
        def get_products(self) -> list[Any]:
            ...

    # WHEN
    with Store() as api:
        first_result = api.get_products()

    # THEN
    assert PRODUCTS == first_result
    client.request.assert_called_once()

    # WHEN
    client.request.reset_mock()
    with Store() as api:
        second_result = api.get_products()

    # THEN
    assert PRODUCTS == second_result
    client.request.assert_not_called()
