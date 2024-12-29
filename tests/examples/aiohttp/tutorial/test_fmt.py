from typing import Annotated, Any

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
    async def get_todos_by_user(
        self, user_id: int, completed: Annotated[bool, api_ref(fmt=Params.bool)]
    ) -> list[Todo]:
        ...

    @endpoint("/todos")
    async def post_todo(self, todo: Annotated[Todo, api_ref("body", fmt=Params.todo)]) -> Todo:
        ...


@pytest.mark.asyncio()
async def test_todos_get_by_user() -> None:
    # WHEN
    async with JsonPlaceholderClient() as client:
        todos = await client.get_todos_by_user(1, completed=True)

    # THEN
    assert len(todos) > 0


@pytest.mark.asyncio()
async def test_post_todo() -> None:
    # GIVEN
    new_todo = Todo.model_construct(user_id=1, id=201, title="test post todo", completed=False)

    # WHEN
    async with JsonPlaceholderClient() as client:
        created_todo = await client.post_todo(new_todo)

    # THEN
    assert created_todo == new_todo
