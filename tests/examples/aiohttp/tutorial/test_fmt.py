from typing import Any

import pytest
from aiohttp import ClientSession
from meatie import endpoint
from meatie_aiohttp import Client
from pydantic import BaseModel, Field


class Todo(BaseModel):
    user_id: int = Field(alias="userId")
    id: int
    title: str
    completed: bool


class Params:
    @staticmethod
    def bool(value: bool) -> str:
        return str(value).lower()

    @staticmethod
    def todo(value: Todo) -> dict[str, Any]:
        return value.model_dump(by_alias=True)


class JsonPlaceholderClient(Client):
    def __init__(self) -> None:
        super().__init__(ClientSession(base_url="https://jsonplaceholder.typicode.com"))

    @endpoint("/users/{user_id}/todos")
    async def get_todos_by_user(self, user_id: int) -> list[Todo]:
        ...


@pytest.mark.asyncio()
async def test_todos_get_by_user() -> None:
    # WHEN
    async with JsonPlaceholderClient() as client:
        todos = await client.get_todos_by_user(1)

    # THEN
    assert len(todos) > 0
