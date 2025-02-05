#  Copyright 2023 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
import json
from typing import Annotated, Any

import pytest
from aiohttp import ClientSession
from pydantic import BaseModel, Field

from meatie import AsyncResponse, api_ref, body, endpoint
from meatie_aiohttp import Client


class Todo(BaseModel):
    user_id: int = Field(alias="userId")
    id: int
    title: str
    completed: bool


async def get_json(response: AsyncResponse) -> Any:
    text = await response.text()
    return json.loads(text)


class JsonPlaceholderClient(Client):
    def __init__(self) -> None:
        super().__init__(ClientSession(base_url="https://jsonplaceholder.typicode.com"))

    @endpoint("/todos", body(json=get_json))
    async def post_todo(self, todo: Annotated[Todo, api_ref("body")]) -> Todo: ...


@pytest.mark.asyncio()
async def test_post_todo() -> None:
    # GIVEN
    new_todo = Todo.model_construct(user_id=1, id=201, title="test post todo", completed=False)
    async with JsonPlaceholderClient() as client:
        # WHEN
        created_todo = await client.post_todo(new_todo)

    # THEN
    assert created_todo == new_todo
