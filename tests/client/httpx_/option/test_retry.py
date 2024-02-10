#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

from http import HTTPStatus
from typing import Any
from unittest.mock import Mock, call

import pytest
from meatie import (
    ResponseError,
    RetryError,
    after_attempt,
    endpoint,
    exponential,
    retry,
)
from meatie_httpx import Client
from mock_tools import HttpxMockTools
from requests import Session

PRODUCTS = [{"name": "headphones"}]


def test_no_retry_on_success_status(mock_tools: HttpxMockTools) -> None:
    # GIVEN
    session = mock_tools.client_with_json_response(json=PRODUCTS, status=HTTPStatus.OK)

    class Store(Client):
        def __init__(self) -> None:
            super().__init__(session)

        @endpoint("/api/v1/products", retry())
        def get_products(self) -> list[Any]:
            ...

    # WHEN
    with Store() as api:
        result = api.get_products()

    # THEN
    assert PRODUCTS == result
    session.request.assert_called_once()


def test_no_retry_on_bad_request(mock_tools: HttpxMockTools) -> None:
    # GIVEN
    client = mock_tools.client_with_json_client_response_error(HTTPStatus.BAD_REQUEST)

    class Store(Client):
        def __init__(self) -> None:
            super().__init__(client)

        @endpoint("/api/v1/products", retry())
        def get_products(self) -> list[Any]:
            ...

    # WHEN
    with pytest.raises(ResponseError):
        with Store() as api:
            api.get_products()

    # THEN
    client.request.assert_called_once()


def test_can_retry(mock_tools: HttpxMockTools) -> None:
    # GIVEN
    too_many_requests_response = mock_tools.json_response({}, HTTPStatus.TOO_MANY_REQUESTS)
    ok_response = mock_tools.json_response(json=PRODUCTS)
    session = Mock(
        spec=Session, request=Mock(side_effect=[too_many_requests_response, ok_response])
    )

    class Store(Client):
        def __init__(self) -> None:
            super().__init__(session)

        @endpoint("/api/v1/products", retry())
        def get_products(self) -> list[Any]:
            ...

    # WHEN
    with Store() as api:
        api.get_products()

    # THEN
    calls = session.request.call_args_list
    assert [call("GET", "/api/v1/products"), call("GET", "/api/v1/products")] == calls


def test_can_throw_rate_limit_exceeded(mock_tools: HttpxMockTools) -> None:
    # GIVEN
    response = mock_tools.json_response({}, HTTPStatus.TOO_MANY_REQUESTS)
    session = mock_tools.client_wrap_response(response)
    sleep_func = Mock()
    attempts = 5

    class Store(Client):
        def __init__(self) -> None:
            super().__init__(session)

        @endpoint(
            "/api/v1/products",
            retry(wait=exponential(), stop=after_attempt(attempts), sleep_func=sleep_func),
        )
        def get_products(self) -> list[Any]:
            ...

    # WHEN
    with pytest.raises(RetryError):
        with Store() as api:
            api.get_products()

    # THEN
    sleep_func.assert_called()
    assert session.request.call_count == attempts
