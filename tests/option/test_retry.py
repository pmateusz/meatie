#  Copyright 2023 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

from http import HTTPStatus
from typing import Any
from unittest.mock import Mock, call, patch

import pytest
from meatie import (
    MeatieError,
    ResponseError,
    Retry,
    StopAfter,
    WaitExponential,
    endpoint,
)
from meatie_requests import RequestsClient
from requests import Session

from tests.conftest import MockTools

PRODUCTS = [{"name": "headphones"}]


def test_no_retry_on_success_status(mock_tools: MockTools) -> None:
    # GIVEN
    session = mock_tools.session_with_json_response(json=PRODUCTS, status=HTTPStatus.OK)

    class Store(RequestsClient):
        def __init__(self) -> None:
            super().__init__(session)

        @endpoint("/api/v1/products", Retry())
        def get_products(self) -> list[Any]:
            ...

    # WHEN
    with Store() as api:
        result = api.get_products()

    # THEN
    assert PRODUCTS == result
    session.request.assert_called_once()


def test_no_retry_on_bad_request(mock_tools: MockTools) -> None:
    # GIVEN
    session = mock_tools.session_with_json_client_response_error(HTTPStatus.BAD_REQUEST)

    class Store(RequestsClient):
        def __init__(self) -> None:
            super().__init__(session)

        @endpoint("/api/v1/products", Retry())
        def get_products(self) -> list[Any]:
            ...

    # WHEN
    with pytest.raises(ResponseError):
        with Store() as api:
            api.get_products()

    # THEN
    session.request.assert_called_once()


def test_can_retry(mock_tools: MockTools) -> None:
    # GIVEN
    too_many_requests_response = mock_tools.json_response({}, HTTPStatus.TOO_MANY_REQUESTS)
    ok_response = mock_tools.json_response(json=PRODUCTS)
    session = Mock(
        spec=Session, request=Mock(side_effect=[too_many_requests_response, ok_response])
    )

    class Store(RequestsClient):
        def __init__(self) -> None:
            super().__init__(session)

        @endpoint("/api/v1/products", Retry())
        def get_products(self) -> list[Any]:
            ...

    # WHEN
    with Store() as api:
        api.get_products()

    # THEN
    calls = session.request.call_args_list
    assert [call("GET", "/api/v1/products"), call("GET", "/api/v1/products")] == calls


def test_can_throw_rate_limit_exceeded(mock_tools: MockTools) -> None:
    # GIVEN
    response = mock_tools.json_response({}, HTTPStatus.TOO_MANY_REQUESTS)
    session = mock_tools.session_wrap_response(response)
    attempts = 5

    class Store(RequestsClient):
        def __init__(self) -> None:
            super().__init__(session)

        @endpoint(
            "/api/v1/products",
            Retry(wait=WaitExponential(), stop=StopAfter(attempts)),
        )
        def get_products(self) -> list[Any]:
            ...

    # WHEN
    with pytest.raises(MeatieError):
        with Store() as api, patch("time.sleep") as sleep_mock:
            api.get_products()

    # THEN
    sleep_mock.assert_called()
    assert session.request.call_count == attempts
