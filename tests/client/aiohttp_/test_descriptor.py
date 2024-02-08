#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

from typing import Any, Optional
from unittest.mock import ANY, Mock

import pytest
from meatie import Request, endpoint
from meatie.aio import AsyncEndpointDescriptor
from meatie.aio.descriptor import AsyncContext
from meatie.internal.template import RequestTemplate
from meatie.internal.types import AsyncClient
from meatie_aiohttp import AiohttpClient

from tests.client.aiohttp_.mock_tools import MockTools

PRODUCTS = [{"name": "Pencil"}, {"name": "Headphones"}]


@pytest.mark.asyncio()
async def test_get_without_parameters(mock_tools: MockTools) -> None:
    # GIVEN
    session = mock_tools.session_with_json_response(json=PRODUCTS)

    class Store(AiohttpClient):
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

    class Store(AiohttpClient):
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


@pytest.mark.asyncio()
async def test_get_with_default_parameter(mock_tools: MockTools) -> None:
    # GIVEN
    session = mock_tools.session_with_json_response(json=PRODUCTS)

    class Store(AiohttpClient):
        def __init__(self) -> None:
            super().__init__(session)

        @endpoint("/api/v1/products")
        async def get_products(self, limit: int = 100) -> list[Any]:
            ...

    # WHEN
    async with Store() as api:
        await api.get_products()

    # THEN
    session.request.assert_awaited_once_with("GET", "/api/v1/products", params={"limit": 100})


@pytest.mark.asyncio()
async def test_get_with_skip_unset_optional_parameter(mock_tools: MockTools) -> None:
    # GIVEN
    session = mock_tools.session_with_json_response(json=PRODUCTS)

    class Store(AiohttpClient):
        def __init__(self) -> None:
            super().__init__(session)

        @endpoint("/api/v1/products")
        async def get_products(self, category: Optional[str] = None) -> list[Any]:
            ...

    # WHEN
    async with Store() as api:
        await api.get_products()

    # THEN
    session.request.assert_awaited_once_with("GET", "/api/v1/products")


@pytest.mark.asyncio()
async def test_get_with_skip_optional_parameter_set_to_none(mock_tools: MockTools) -> None:
    # GIVEN
    session = mock_tools.session_with_json_response(json=PRODUCTS)

    class Store(AiohttpClient):
        def __init__(self) -> None:
            super().__init__(session)

        @endpoint("/api/v1/products")
        async def get_products(self, category: Optional[str] = None) -> list[Any]:
            ...

    # WHEN
    async with Store() as api:
        await api.get_products(category=None)

    # THEN
    session.request.assert_awaited_once_with("GET", "/api/v1/products")


@pytest.mark.asyncio()
async def test_get_with_send_optional_parameter(mock_tools: MockTools) -> None:
    # GIVEN
    session = mock_tools.session_with_json_response(json=PRODUCTS)

    class Store(AiohttpClient):
        def __init__(self) -> None:
            super().__init__(session)

        @endpoint("/api/v1/products")
        async def get_products(self, category: Optional[str] = None) -> list[Any]:
            ...

    # WHEN
    async with Store() as api:
        await api.get_products(category="household")

    # THEN
    session.request.assert_awaited_once_with(
        "GET", "/api/v1/products", params={"category": "household"}
    )


def test_falls_back_to_get_if_method_name_cannot_be_inferred() -> None:
    # GIVEN
    template = Mock(spec=RequestTemplate, method=None)
    descriptor = AsyncEndpointDescriptor[Any, Any](template, ANY)

    # WHEN
    descriptor.__set_name__(object, "list_products")

    # THEN
    assert "GET" == template.method


@pytest.mark.asyncio()
async def test_context_without_operators_fails_on_proceed() -> None:
    # GIVEN
    client = Mock(spec=AsyncClient)
    request = Mock(spec=Request)
    context = AsyncContext[list[Any]](client, [], request)

    # WHEN
    with pytest.raises(RuntimeError) as exc_info:
        await context.proceed()

    # THEN
    exc = exc_info.value
    assert exc.args == ("No more step to process request",)
