from typing import Annotated

import pytest
from aiohttp import ClientSession
from meatie import Request, api_ref, endpoint, private
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

    @endpoint("/todos", private)
    async def get_todos(self, user_id: Annotated[int, api_ref("userId")] = None) -> list[Todo]:
        ...

    async def authenticate(self, request: Request) -> None:
        request.headers["Authorization"] = "Bearer bWVhdGll"


@pytest.mark.asyncio()
async def test_todos_filter_by_user() -> None:
    # WHEN
    async with JsonPlaceholderClient() as client:
        todos = await client.get_todos(user_id=1)

    # THEN
    assert all(todo.user_id == 1 for todo in todos)
