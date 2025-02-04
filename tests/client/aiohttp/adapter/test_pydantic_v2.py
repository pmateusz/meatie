#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler
from typing import Annotated, Any, Optional, Union
from typing_extensions import Literal

import pytest

from aiohttp import ClientSession
from http_test import HTTPTestServer, Handler
from meatie import AsyncResponse, api_ref, endpoint
from meatie_aiohttp import Client

pydantic = pytest.importorskip("pydantic", minversion="2.0.0")


@pytest.mark.asyncio()
async def test_post_request_body_with_fmt(http_server: HTTPTestServer) -> None:
    # GIVEN
    class Request(pydantic.BaseModel):
        data: Optional[dict[str, Any]]

    def handler(request: BaseHTTPRequestHandler) -> None:
        content_length = request.headers.get("Content-Length", "0")
        raw_body = request.rfile.read(int(content_length))
        body = json.loads(raw_body.decode("utf-8"))

        if body.get("data") is not None:
            request.send_response(HTTPStatus.BAD_REQUEST)
        else:
            request.send_response(HTTPStatus.OK)
        request.end_headers()

    http_server.handler = handler

    def dump_body(model: pydantic.BaseModel) -> str:
        return model.model_dump_json(by_alias=True, exclude_none=True)

    class TestClient(Client):
        @endpoint("/")
        async def post_request(self, body: Annotated[Request, api_ref(fmt=dump_body)]) -> AsyncResponse:
            ...

    # WHEN
    async with TestClient(ClientSession(http_server.base_url)) as client:
        response = await client.post_request(Request(data=None))

    # THEN
    assert response.status == HTTPStatus.OK


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
        async def get_todo(self) -> Union[TodoV1, TodoV2]:
            ...

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
        async def get_todo(self) -> pydantic.TypeAdapter(Union[TodoV1, TodoV2]):
            ...

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
        async def get_instrument(self) -> Instrument:
            ...

    # WHEN
    async with ExchangeClient(ClientSession(http_server.base_url)) as client:
        instrument = await client.get_instrument()

    # THEN
    assert isinstance(instrument, Spot)
    assert instrument.instrument_type == "spot"
    assert instrument.base == "BTC"
    assert instrument.quote == "USDT"
