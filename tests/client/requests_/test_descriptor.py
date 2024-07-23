#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
from enum import Enum
from typing import Any, Optional, Literal, Annotated
from unittest.mock import ANY, Mock

import pytest
from meatie import Request, endpoint, api_ref
from meatie.descriptor import Context, EndpointDescriptor
from meatie.internal.template import RequestTemplate
from meatie_requests import Client

from tests.conftest import MockTools

PRODUCTS = [{"name": "Pencil"}, {"name": "Headphones"}]


def test_get_without_parameters(mock_tools: MockTools) -> None:
    # GIVEN
    session = mock_tools.session_with_json_response(json=PRODUCTS)

    class Store(Client):
        def __init__(self) -> None:
            super().__init__(session)

        @endpoint("/api/v1/products")
        def get_products(self) -> list[Any]:
            ...

    # WHEN
    with Store() as api:
        result = api.get_products()

    # THEN
    assert PRODUCTS == result
    session.request.assert_called_once_with("GET", "/api/v1/products")


def test_post_with_body(mock_tools: MockTools) -> None:
    # GIVEN
    session = mock_tools.session_with_json_response(json=None)

    class Store(Client):
        def __init__(self) -> None:
            super().__init__(session)

        @endpoint("/api/v1/order")
        def post_order(self, body: Any) -> None:
            ...

    # WHEN
    with Store() as api:
        api.post_order(PRODUCTS)

    # THEN
    session.request.assert_called_once_with("POST", "/api/v1/order", json=PRODUCTS)


def test_get_with_default_parameter(mock_tools: MockTools) -> None:
    # GIVEN
    session = mock_tools.session_with_json_response(json=PRODUCTS)

    class Store(Client):
        def __init__(self) -> None:
            super().__init__(session)

        @endpoint("/api/v1/products")
        def get_products(self, limit: int = 100) -> list[Any]:
            ...

    # WHEN
    with Store() as api:
        api.get_products()

    # THEN
    session.request.assert_called_once_with("GET", "/api/v1/products", params={"limit": 100})


def test_get_with_skip_optional_parameter(mock_tools: MockTools) -> None:
    # GIVEN
    session = mock_tools.session_with_json_response(json=PRODUCTS)

    class Status(Enum):
        PENDING = "pending"
        SHIPPED = "shipped"

    class Store(Client):
        def __init__(self) -> None:
            super().__init__(session)

        @endpoint("/api/v1/products")
        def get_products(self,
                         start: Annotated[str, api_ref("t_start")],
                         end: Annotated[str, api_ref("t_end")],
                         status: Status | None,
                         limit: int | None = 100,
                         order: Literal["asc", "desc"] | None = "desc") -> list[Any]:
            ...

    # WHEN
    with Store() as api:
        api.get_products(start="2021-01-01", end="2021-12-31")

    # THEN
    session.request.assert_called_once_with("GET", "/api/v1/products", params={'limit': 100, 'order': 'desc', 't_start': '2021-01-01', 't_end': '2021-12-31'})


def test_get_with_skip_unset_optional_parameter_with_default(mock_tools: MockTools) -> None:
    # GIVEN
    session = mock_tools.session_with_json_response(json=PRODUCTS)

    class Store(Client):
        def __init__(self) -> None:
            super().__init__(session)

        @endpoint("/api/v1/products")
        def get_products(self, category: Optional[str] = None) -> list[Any]:
            ...

    # WHEN
    with Store() as api:
        api.get_products()

    # THEN
    session.request.assert_called_once_with("GET", "/api/v1/products")


def test_get_with_skip_optional_parameter_set_to_none(mock_tools: MockTools) -> None:
    # GIVEN
    session = mock_tools.session_with_json_response(json=PRODUCTS)

    class Store(Client):
        def __init__(self) -> None:
            super().__init__(session)

        @endpoint("/api/v1/products")
        def get_products(self, category: Optional[str] = None) -> list[Any]:
            ...

    # WHEN
    with Store() as api:
        api.get_products(category=None)

    # THEN
    session.request.assert_called_once_with("GET", "/api/v1/products")


def test_get_with_send_optional_parameter(mock_tools: MockTools) -> None:
    # GIVEN
    session = mock_tools.session_with_json_response(json=PRODUCTS)

    class Store(Client):
        def __init__(self) -> None:
            super().__init__(session)

        @endpoint("/api/v1/products")
        def get_products(self, category: Optional[str] = None) -> list[Any]:
            ...

    # WHEN
    with Store() as api:
        api.get_products(category="household")

    # THEN
    session.request.assert_called_once_with(
        "GET", "/api/v1/products", params={"category": "household"}
    )


def test_falls_back_to_get_if_method_name_cannot_be_inferred() -> None:
    # GIVEN
    template = Mock(spec=RequestTemplate, method=None)
    descriptor = EndpointDescriptor[Any, Any](template, ANY)

    # WHEN
    descriptor.__set_name__(object, "list_products")

    # THEN
    assert "GET" == template.method


def test_context_without_operators_fails_on_proceed() -> None:
    # GIVEN
    client = Mock(spec=Client)
    request = Mock(spec=Request)
    context = Context[list[Any]](client, [], request)

    # WHEN
    with pytest.raises(RuntimeError) as exc_info:
        context.proceed()

    # THEN
    exc = exc_info.value
    assert exc.args == ("No more step to process request",)
