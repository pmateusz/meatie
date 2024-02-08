#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

from typing import Any, cast

from client.requests_.mock_tools import MockTools
from meatie import INF, Cache, endpoint
from meatie_requests import RequestsClient
from requests import Session


PRODUCTS = [{"name": "pencil"}, {"name": "headphones"}]


def test_local_cache_is_isolated(mock_tools: MockTools) -> None:
    # GIVEN
    session = mock_tools.session_with_json_response(json=PRODUCTS)

    class Store(RequestsClient):
        def __init__(self) -> None:
            super().__init__(cast(Session, session))

        @endpoint("/api/v1/products", Cache(ttl=INF, shared=False))
        def get_products(self) -> list[Any]:
            ...

    # WHEN
    with Store() as api:
        first_result = api.get_products()

    # THEN
    assert PRODUCTS == first_result
    session.request.assert_called_once()

    # WHEN
    session.request.reset_mock()
    with Store() as api:
        second_result = api.get_products()

    # THEN
    assert PRODUCTS == second_result
    session.request.assert_called_once()


def test_global_cache_is_shared(mock_tools: MockTools) -> None:
    # GIVEN
    session = mock_tools.session_with_json_response(json=PRODUCTS)

    class Store(RequestsClient):
        def __init__(self) -> None:
            super().__init__(session)

        @endpoint("/api/v1/products", Cache(ttl=INF, shared=True))
        def get_products(self) -> list[Any]:
            ...

    # WHEN
    with Store() as api:
        first_result = api.get_products()

    # THEN
    assert PRODUCTS == first_result
    session.request.assert_called_once()

    # WHEN
    session.request.reset_mock()
    with Store() as api:
        second_result = api.get_products()

    # THEN
    assert PRODUCTS == second_result
    session.request.assert_not_called()
