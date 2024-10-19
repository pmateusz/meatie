#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
import datetime
import json
from dataclasses import dataclass
from typing import Annotated, Any, Optional
from unittest.mock import ANY, Mock

import pytest
from meatie import Request, api_ref, endpoint
from meatie.aio import AsyncContext, AsyncEndpointDescriptor
from meatie.internal.template import RequestTemplate
from meatie.internal.types import AsyncClient
from meatie_aiohttp import Client

PRODUCTS = [{"name": "Pencil"}, {"name": "Headphones"}]


@pytest.mark.asyncio()
async def test_get_without_parameters(mock_tools) -> None:
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
async def test_get_with_formatter(mock_tools) -> None:
    # GIVEN
    session = mock_tools.session_with_json_response(json=PRODUCTS)

    def format_date(date: datetime.datetime) -> str:
        return date.strftime("%Y-%m-%d")

    class Store(Client):
        def __init__(self) -> None:
            super().__init__(session)

        @endpoint("/api/v1/transactions")
        async def get_transactions(
            self, since: Annotated[datetime.datetime, api_ref(fmt=format_date)]
        ) -> list[Any]:
            ...

    # WHEN
    async with Store() as api:
        result = await api.get_transactions(since=datetime.datetime(2006, 1, 2))

    # THEN
    assert PRODUCTS == result
    session.request.assert_awaited_once_with(
        "GET", "/api/v1/transactions", params={"since": "2006-01-02"}
    )


@pytest.mark.asyncio()
async def test_get_with_marshaller(mock_tools) -> None:
    # GIVEN
    session = mock_tools.session_with_json_response(json=PRODUCTS)

    @dataclass
    class TimeRange:
        start: datetime.datetime
        end: datetime.datetime

    layout = "%Y-%m-%d"

    def format_time_range(time_range: TimeRange) -> dict[str, str]:
        return {
            "since": time_range.start.strftime(layout),
            "until": time_range.end.strftime(layout),
        }

    class Store(Client):
        def __init__(self) -> None:
            super().__init__(session)

        @endpoint("/api/v1/transactions")
        async def get_transactions(
            self, time_range: Annotated[TimeRange, api_ref(unwrap=format_time_range)]
        ) -> list[Any]:
            ...

    # WHEN
    async with Store() as api:
        result = await api.get_transactions(
            time_range=TimeRange(start=datetime.datetime(2006, 1, 2),
                                 end=datetime.datetime(2006, 1, 3)))

    # THEN
    assert PRODUCTS == result
    session.request.assert_awaited_once_with(
        "GET", "/api/v1/transactions", params={"since": "2006-01-02", "until": "2006-01-03"}
    )


@pytest.mark.asyncio()
async def test_post_with_body(mock_tools) -> None:
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


@pytest.mark.asyncio()
async def test_post_with_bytes_body(mock_tools) -> None:
    # GIVEN
    session = mock_tools.session_with_json_response(json=None)

    class Store(Client):
        def __init__(self) -> None:
            super().__init__(session)

        @endpoint("/api/v1/order")
        async def post_order(self, body: bytes) -> None:
            ...

    # WHEN
    async with Store() as api:
        await api.post_order(json.dumps(PRODUCTS, separators=(",", ":")).encode())

    # THEN
    session.request.assert_awaited_once_with(
        "POST", "/api/v1/order", json=b'[{"name":"Pencil"},{"name":"Headphones"}]'
    )


@pytest.mark.asyncio()
async def test_handles_optional_parameters_with_default_name(mock_tools) -> None:
    # GIVEN
    session = mock_tools.session_with_json_response(json=None)

    def int_timestamp(value: datetime.datetime) -> int:
        return int(value.timestamp())

    class Store(Client):
        def __init__(self) -> None:
            super().__init__(session)

        @endpoint("/api/v1/orders")
        async def get_orders(
            self,
            begin: Annotated[datetime.datetime, api_ref(fmt=int_timestamp)] = None,
            end: Annotated[datetime.datetime, api_ref(fmt=int_timestamp)] = None,
        ) -> list[Any]:
            ...

    begin = datetime.datetime(2024, 8, 1)
    end = datetime.datetime(2024, 8, 3)

    # WHEN
    async with Store() as api:
        await api.get_orders(begin, end)

    # THEN
    session.request.assert_awaited_once_with(
        "GET", "/api/v1/orders", params={"begin": int_timestamp(begin), "end": int_timestamp(end)}
    )


@pytest.mark.asyncio()
async def test_get_with_default_parameter(mock_tools) -> None:
    # GIVEN
    session = mock_tools.session_with_json_response(json=PRODUCTS)

    class Store(Client):
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
async def test_get_with_skip_unset_optional_parameter(mock_tools) -> None:
    # GIVEN
    session = mock_tools.session_with_json_response(json=PRODUCTS)

    class Store(Client):
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
async def test_get_with_skip_optional_parameter_set_to_none(mock_tools) -> None:
    # GIVEN
    session = mock_tools.session_with_json_response(json=PRODUCTS)

    class Store(Client):
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
async def test_get_with_send_optional_parameter(mock_tools) -> None:
    # GIVEN
    session = mock_tools.session_with_json_response(json=PRODUCTS)

    class Store(Client):
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
