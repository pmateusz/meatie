#  Copyright 2023 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
from typing import Annotated

import pytest
from aiohttp import ClientSession
from meatie import AsyncResponse, HttpStatusError, api_ref, body, endpoint
from meatie_aiohttp import Client
from pydantic import BaseModel, Field


class Todo(BaseModel):
    user_id: int = Field(alias="userId")
    id: int
    title: str
    completed: bool


async def get_error(response: AsyncResponse) -> Exception | None:
    if 200 <= response.status < 300:
        return None

    return HttpStatusError(response)


class JsonPlaceholderClient(Client):
    def __init__(self) -> None:
        super().__init__(ClientSession(base_url="https://jsonplaceholder.typicode.com"))

    @endpoint("/todos", body(error=get_error))
    async def get_todos(self, user_id: Annotated[int, api_ref("userId")] = None) -> list[Todo]:
        ...


@pytest.mark.asyncio()
async def test_todos_filter_by_user() -> None:
    # WHEN
    async with JsonPlaceholderClient() as client:
        todos = await client.get_todos(user_id=1)

    # THEN
    assert all(todo.user_id == 1 for todo in todos)
