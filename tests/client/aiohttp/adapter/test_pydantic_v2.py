#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
from http import HTTPStatus
from typing import Annotated, Union

import pytest
from aiohttp import ClientSession
from http_test import Handler, HTTPTestServer
from http_test.handlers import echo_json_handler
from typing_extensions import Literal

from meatie import api_ref, endpoint
from meatie_aiohttp import Client

pydantic = pytest.importorskip("pydantic", minversion="2.0.0")


class Todo(pydantic.BaseModel):
    user_id: int = pydantic.Field(alias="userId")
    id: int
    title: str
    completed: bool


class Params:
    @staticmethod
    def todo(value: Todo) -> dict:
        return value.model_dump(by_alias=True)


class JsonPlaceholderClient(Client):
    def __init__(self, base_url: str) -> None:
        super().__init__(ClientSession(base_url=base_url))

    @endpoint("/todos")
    async def post_todo_as_dict(
        self, todo: Annotated[Todo, api_ref("body", fmt=lambda data: data.model_dump(by_alias=True))]
    ) -> Todo: ...


@pytest.mark.asyncio()
async def test_post_request_body_with_fmt_as_dict(http_server: HTTPTestServer) -> None:
    # GIVEN
    http_server.handler = echo_json_handler

    # WHEN
    async with JsonPlaceholderClient(http_server.base_url) as client:
        todo = await client.post_todo_as_dict(Todo(userId=123, id=456, title="abc", completed=True))

    # THEN
    assert todo.user_id == 123


class TodoV1(pydantic.BaseModel):
    user_id: int = pydantic.Field(alias="userId")
    id: int
    title: str


class TodoV2(pydantic.BaseModel):
    user_id: int = pydantic.Field(alias="userId")
    id: int
    title: str
    completed: bool


@pytest.mark.asyncio()
async def test_can_handle_union_return_type(http_server: HTTPTestServer) -> None:
    # GIVEN
    def handler(request: Handler) -> None:
        request.send_json(HTTPStatus.OK, {"userId": 1, "id": 1, "title": "Task v2", "completed": False})

    http_server.handler = handler

    class TodoClient(Client):
        @endpoint("/")
        async def get_todo(self) -> Union[TodoV1, TodoV2]: ...

    # WHEN
    async with TodoClient(ClientSession(http_server.base_url)) as client:
        task = await client.get_todo()

    # THEN
    assert isinstance(task, TodoV2)
    assert task.user_id == 1
    assert task.id == 1
    assert task.title == "Task v2"
    assert task.completed is False


@pytest.mark.asyncio()
async def test_can_handle_type_adapter_return_type(http_server: HTTPTestServer) -> None:
    # GIVEN
    def handler(request: Handler) -> None:
        request.send_json(HTTPStatus.OK, {"userId": 1, "id": 1, "title": "Task v1"})

    http_server.handler = handler

    class TodoClient(Client):
        @endpoint("/")
        async def get_todo(self) -> pydantic.TypeAdapter(Union[TodoV1, TodoV2]): ...

    # WHEN
    async with TodoClient(ClientSession(http_server.base_url)) as client:
        task = await client.get_todo()

    # THEN
    assert isinstance(task, TodoV1)
    assert task.user_id == 1
    assert task.id == 1
    assert task.title == "Task v1"


class Currency(pydantic.BaseModel):
    instrument_type: Literal["currency"]
    symbol: str


class Spot(pydantic.BaseModel):
    instrument_type: Literal["spot"]
    symbol: str
    base: str
    quote: str


class Perpetual(pydantic.BaseModel):
    instrument_type: Literal["perpetual"]
    symbol: str
    base: str
    quote: str
    settlement: str


Instrument = Annotated[Union[Currency, Spot, Perpetual], pydantic.Field(discriminator="instrument_type")]


@pytest.mark.asyncio()
async def test_can_handle_type_adapter_with_discriminated_column(http_server: HTTPTestServer) -> None:
    # GIVEN
    def handler(request: Handler) -> None:
        request.send_json(
            HTTPStatus.OK, {"instrument_type": "spot", "symbol": "BTC/USDT", "base": "BTC", "quote": "USDT"}
        )

    http_server.handler = handler

    class ExchangeClient(Client):
        @endpoint("/")
        async def get_instrument(self) -> Instrument: ...

    # WHEN
    async with ExchangeClient(ClientSession(http_server.base_url)) as client:
        instrument = await client.get_instrument()

    # THEN
    assert isinstance(instrument, Spot)
    assert instrument.instrument_type == "spot"
    assert instrument.base == "BTC"
    assert instrument.quote == "USDT"


@pytest.mark.asyncio()
async def test_can_handle_list_of_discriminated_union(http_server: HTTPTestServer) -> None:
    # GIVEN
    def handler(request: Handler) -> None:
        request.send_json(
            HTTPStatus.OK,
            [
                {"instrument_type": "currency", "symbol": "USD"},
                {"instrument_type": "spot", "symbol": "BTC/USDT", "base": "BTC", "quote": "USDT"},
                {"instrument_type": "perpetual", "symbol": "BTC-PERP", "base": "BTC", "quote": "USDT", "settlement": "USDT"},
            ],
        )

    http_server.handler = handler

    class ExchangeClient(Client):
        @endpoint("/")
        async def get_instruments(self) -> list[Instrument]: ...

    # WHEN
    async with ExchangeClient(ClientSession(http_server.base_url)) as client:
        instruments = await client.get_instruments()

    # THEN
    assert len(instruments) == 3
    assert isinstance(instruments[0], Currency)
    assert isinstance(instruments[1], Spot)
    assert isinstance(instruments[2], Perpetual)
