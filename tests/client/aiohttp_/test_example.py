#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

# mypy: disable-error-code="valid-type"

from decimal import Decimal
from http import HTTPStatus
from typing import Annotated, Any, Callable
from unittest.mock import AsyncMock, Mock, call, patch

import pytest
from aiohttp import ClientSession
from meatie import (
    MINUTE,
    ApiRef,
    Limiter,
    Rate,
    Request,
    cache,
    endpoint,
    exponential,
    has_status,
    limit,
    private,
    retry,
)
from meatie_aiohttp import AiohttpClient
from mock_tools import AiohttpMockTools

pydantic = pytest.importorskip("pydantic")
BaseModel: type = pydantic.BaseModel
PositiveInt = pydantic.PositiveInt


class Product(BaseModel):
    id: int
    name: str


class BasketItem(BaseModel):
    product_id: int
    quantity: PositiveInt


class Basket(BaseModel):
    items: list[BasketItem]


class BasketQuote(BaseModel):
    id: int
    value: Decimal
    currency: str


class OnlineStore(AiohttpClient):
    def __init__(self, session: ClientSession) -> None:
        super().__init__(session)

    @endpoint("/api/v1/products")
    async def get_products(self) -> list[Product]:
        ...

    @endpoint("/api/v1/quote/request")
    async def post_request_quote(self, basket: Annotated[Basket, ApiRef("body")]) -> BasketQuote:
        ...

    @endpoint("/api/v1/quote/{quote_id}/accept", method="POST")
    async def accept_quote(self, quote_id: int) -> None:
        ...


@pytest.mark.asyncio()
async def test_plain_example(dump_model: Callable[[Any], Any]) -> None:
    # GIVEN
    class OnlineStore(AiohttpClient):
        def __init__(self, session: ClientSession) -> None:
            super().__init__(session)

        @endpoint("/api/v1/products")
        async def get_products(self) -> list[Product]:
            ...

        @endpoint("/api/v1/quote/request")
        async def post_request_quote(
            self, basket: Annotated[Basket, ApiRef("body")]
        ) -> BasketQuote:
            ...

        @endpoint("/api/v1/quote/{quote_id}/accept", method="POST")
        async def accept_quote(self, quote_id: int) -> None:
            ...

    # GIVEN
    products = [Product(id=1, name="Headphones"), Product(id=2, name="Keyboard")]
    session = Mock(spec=ClientSession)
    session.request = AsyncMock(return_value=AsyncMock(json=AsyncMock(return_value=products)))

    async with OnlineStore(session) as api:
        # WHEN
        products_result = await api.get_products()

        # THEN
        assert products == products_result
        session.request.assert_awaited_once_with("GET", "/api/v1/products")

        # GIVEN
        basket = Basket(items=[BasketItem(product_id=1, quantity=2)])
        quote = BasketQuote(id=1, value=Decimal(2_000), currency="USD")
        session.request = AsyncMock(return_value=AsyncMock(json=AsyncMock(return_value=quote)))

        # WHEN
        quote_result = await api.post_request_quote(basket)

        # THEN
        assert quote == quote_result
        session.request.assert_awaited_once_with(
            "POST", "/api/v1/quote/request", json=dump_model(basket)
        )

        # GIVEN
        session.request = AsyncMock(return_value=AsyncMock())

        # WHEN
        await api.accept_quote(quote_result.id)

        # THEN
        session.request.assert_awaited_once_with("POST", "/api/v1/quote/1/accept")


@pytest.mark.asyncio()
async def test_private_endpoint_example(dump_model: Callable[[Any], Any]) -> None:
    # GIVEN
    class OnlineStore(AiohttpClient):
        def __init__(self, session: ClientSession) -> None:
            super().__init__(session)

        @endpoint("/api/v1/quote/request", private)
        async def post_request_quote(
            self, basket: Annotated[Basket, ApiRef("body")]
        ) -> BasketQuote:
            ...

        async def authenticate(self, request: Request) -> None:
            request.headers["api-key"] = "123"

    # GIVEN
    quote = BasketQuote(id=1, value=Decimal(2_000), currency="USD")
    session = Mock(spec=ClientSession)

    async with OnlineStore(session) as api:
        # GIVEN
        basket = Basket(items=[BasketItem(product_id=1, quantity=2)])
        session.request = AsyncMock(return_value=AsyncMock(json=AsyncMock(return_value=quote)))

        # WHEN
        quote_result = await api.post_request_quote(basket)

        # THEN
        assert quote == quote_result
        session.request.assert_awaited_once_with(
            "POST", "/api/v1/quote/request", json=dump_model(basket), headers={"api-key": "123"}
        )


@pytest.mark.asyncio()
async def test_cache_endpoint_example() -> None:
    # GIVEN
    class OnlineStore(AiohttpClient):
        def __init__(self, session: ClientSession) -> None:
            super().__init__(session)

        @endpoint("/api/v1/products", cache(ttl=5 * MINUTE))
        async def get_products(self) -> list[Product]:
            ...

    # GIVEN
    products = [Product(id=1, name="Headphones"), Product(id=2, name="Keyboard")]
    session = Mock(spec=ClientSession)

    async with OnlineStore(session) as api:
        # GIVEN
        session.request = AsyncMock(return_value=AsyncMock(json=AsyncMock(return_value=products)))

        # WHEN
        products_request_1 = await api.get_products()

        # THEN
        assert products == products_request_1
        session.request.assert_awaited_once_with("GET", "/api/v1/products")

        # GIVEN
        session.request.reset_mock()

        # WHEN
        products_request_2 = await api.get_products()

        # THEN
        assert products == products_request_2
        session.request.assert_not_called()


@pytest.mark.asyncio()
async def test_retry_example(
    mock_tools: AiohttpMockTools, dump_model: Callable[[Any], Any]
) -> None:
    # GIVEN
    class OnlineStore(AiohttpClient):
        def __init__(self, session: ClientSession) -> None:
            super().__init__(session)

        @endpoint(
            "/api/v1/products",
            retry(
                on=has_status(HTTPStatus.TOO_MANY_REQUESTS),
                wait=exponential(),
                sleep_func=AsyncMock(),
            ),
        )
        async def get_products(self) -> list[Product]:
            ...

    # GIVEN
    products = [Product(id=1, name="Headphones"), Product(id=2, name="Keyboard")]
    session = Mock(spec=ClientSession)

    async with OnlineStore(session) as api:
        # GIVEN
        session.request = AsyncMock(
            side_effect=[
                mock_tools.json_client_response_error(HTTPStatus.TOO_MANY_REQUESTS),
                mock_tools.json_response(dump_model(products)),
            ]
        )

        # WHEN
        result = await api.get_products()

        # THEN
        assert products == result
        session.request.assert_has_calls([call("GET", "/api/v1/products")])


@pytest.mark.asyncio()
async def test_rate_limit_example(
    mock_tools: AiohttpMockTools, dump_model: Callable[[Any], Any]
) -> None:
    # GIVEN
    current_time = 1000
    sleep_func = AsyncMock()

    class OnlineStore(AiohttpClient):
        def __init__(self, session: ClientSession) -> None:
            super().__init__(
                session,
                limiter=Limiter(
                    Rate(tokens_per_sec=1), capacity=60, init_tokens=0, init_time=current_time
                ),
            )

        @endpoint("/api/v1/products", limit(tokens=5, sleep_func=sleep_func))
        async def get_products(self) -> list[Product]:
            ...

    # GIVEN
    products = [Product(id=1, name="Headphones"), Product(id=2, name="Keyboard")]
    session = Mock(spec=ClientSession)

    with patch("time.monotonic") as monotonic_mock:
        monotonic_mock.return_value = current_time

        async with OnlineStore(session) as api:
            # GIVEN
            session.request = AsyncMock(return_value=mock_tools.json_response(dump_model(products)))

            # WHEN
            result = await api.get_products()

            # THEN
            assert products == result
            session.request.assert_awaited_once_with("GET", "/api/v1/products")
            monotonic_mock.assert_called_once()
            sleep_func.assert_awaited_once_with(5)
