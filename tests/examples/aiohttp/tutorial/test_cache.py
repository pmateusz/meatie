from typing import Annotated

import pytest
from aiohttp import ClientSession
from pydantic import BaseModel, Field

from meatie import MINUTE, api_ref, cache, endpoint
from meatie_aiohttp import Client


class Todo(BaseModel):
    user_id: int = Field(alias="userId")
    id: int
    title: str
    completed: bool


class JsonPlaceholderClient(Client):
    def __init__(self) -> None:
        super().__init__(ClientSession(base_url="https://jsonplaceholder.typicode.com"))

    @endpoint("/todos", cache(ttl=MINUTE))
    async def get_todos(self, user_id: Annotated[int, api_ref("userId")] = None) -> list[Todo]: ...


@pytest.mark.asyncio()
async def test_todos_filter_by_user() -> None:
    # WHEN
    async with JsonPlaceholderClient() as client:
        todos = await client.get_todos(user_id=1)

    # THEN
    assert all(todo.user_id == 1 for todo in todos)
