from typing import Annotated, Any

import pytest
from aiohttp import ClientSession
from meatie import api_ref, endpoint, AsyncResponse, body
from meatie_aiohttp import Client
from pydantic import BaseModel, Field
import json


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
    async def get_todos(self, user_id: Annotated[int, api_ref("userId")] = None) -> list[Todo]:
        ...


@pytest.mark.asyncio()
async def test_todos_filter_by_user() -> None:
    # WHEN
    async with JsonPlaceholderClient() as client:
        todos = await client.get_todos(user_id=1)

    # THEN
    assert all(todo.user_id == 1 for todo in todos)
