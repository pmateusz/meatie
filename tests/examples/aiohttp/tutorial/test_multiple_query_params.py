from typing import Annotated

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


class JsonPlaceholderClient(Client):
    def __init__(self) -> None:
        super().__init__(ClientSession(base_url="https://jsonplaceholder.typicode.com"))

    @endpoint("/todos")
    async def get_todos(self, user_ids: Annotated[list[int], api_ref("userId")] = None) -> list[Todo]:
        ...


@pytest.mark.asyncio()
async def test_todos_filter_by_users() -> None:
    # WHEN
    async with JsonPlaceholderClient() as client:
        todos = await client.get_todos(user_ids=[1, 2])

    # THEN
    assert all(todo.user_id in [1, 2] for todo in todos)
