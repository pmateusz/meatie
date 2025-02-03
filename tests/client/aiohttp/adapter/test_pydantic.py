#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
from enum import Enum
from http import HTTPStatus
from typing import Union

import pytest
from aiohttp import ClientSession
from http_test import HTTPTestServer, Handler
from meatie import ParseResponseError, endpoint
from meatie_aiohttp import Client

pydantic = pytest.importorskip("pydantic")
BaseModel: type = pydantic.BaseModel


class ResponseV1(BaseModel):
    status: str


@pytest.mark.asyncio()
async def test_can_parse_pydantic_model(http_server: HTTPTestServer) -> None:
    # GIVEN
    def handler(request: Handler) -> None:
        request.send_json(HTTPStatus.OK, {"status": "ok"})

    http_server.handler = handler

    class TestClient(Client):
        @endpoint("/")
        async def get_response(self) -> ResponseV1:
            ...

    # WHEN
    async with TestClient(ClientSession(http_server.base_url)) as client:
        response = await client.get_response()

    # THEN
    assert ResponseV1(status="ok") == response


@pytest.mark.asyncio()
async def test_can_handle_corrupted_pydantic_model(http_server: HTTPTestServer) -> None:
    # GIVEN
    def handler(request: Handler) -> None:
        request.send_json(HTTPStatus.OK, {"code": "ok"})

    http_server.handler = handler

    class TestClient(Client):
        @endpoint("/")
        async def get_response(self) -> ResponseV1:
            ...

    # WHEN
    with pytest.raises(ParseResponseError) as exc_info:
        async with TestClient(ClientSession(http_server.base_url)) as client:
            await client.get_response()

    # THEN
    exc = exc_info.value
    assert HTTPStatus.OK == exc.response.status


class StatusCode(str, Enum):
    OK = "OK"


class ResponseV2(BaseModel):
    status: StatusCode


@pytest.mark.asyncio()
async def test_can_handle_corrupted_pydantic_model_with_enum(
    http_server: HTTPTestServer,
) -> None:
    # GIVEN
    def handler(request: Handler) -> None:
        request.send_json(HTTPStatus.OK, {"status": "ok"})

    http_server.handler = handler

    class TestClient(Client):
        @endpoint("/")
        async def get_response(self) -> ResponseV2:
            ...

    # WHEN
    with pytest.raises(ParseResponseError) as exc_info:
        async with TestClient(ClientSession(http_server.base_url)) as client:
            await client.get_response()

    # THEN
    exc = exc_info.value
    assert HTTPStatus.OK == exc.response.status


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
