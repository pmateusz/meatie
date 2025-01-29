#  Copyright 2023 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
from dataclasses import dataclass
from typing import Annotated, Any, Self

import pytest
from aiohttp import ClientSession
from meatie import api_ref, endpoint
from meatie_aiohttp import Client
from pydantic import BaseModel, Field


class Todo(BaseModel):
    user_id: int = Field(alias="userId")
    id: int
    title: str
    completed: bool


@dataclass
class TodoParams:
    user_id: int | None = None
    completed: bool | None = None

    @classmethod
    def unwrap(cls, value: Self) -> dict[str, Any]:
        values = {}

        if value.user_id is not None:
            values["userId"] = value.user_id

        if value.completed is not None:
            values["completed"] = str(value.completed).lower()

        return values


class JsonPlaceholderClient(Client):
    def __init__(self) -> None:
        super().__init__(ClientSession(base_url="https://jsonplaceholder.typicode.com"))

    @endpoint("/todos")
    async def get_todos(self, params: Annotated[TodoParams, api_ref(unwrap=TodoParams.unwrap)] = None) -> list[Todo]:
        ...


@pytest.mark.asyncio()
async def test_todos_filter_by_user() -> None:
    # WHEN
    async with JsonPlaceholderClient() as client:
        todos = await client.get_todos(params=TodoParams(user_id=1))

    # THEN
    assert all(todo.user_id == 1 for todo in todos)
