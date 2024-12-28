from typing import Annotated

import pytest
from aiohttp import ClientSession
from meatie import (
    HttpStatusError,
    RetryContext,
    after_attempt,
    api_ref,
    endpoint,
    fixed,
    jit,
    retry,
)
from meatie_aiohttp import Client
from pydantic import BaseModel, Field


class Todo(BaseModel):
    user_id: int = Field(alias="userId")
    id: int
    title: str
    completed: bool


def should_retry(ctx: RetryContext) -> bool:
    if isinstance(ctx.error, HttpStatusError):
        return ctx.error.response.status >= 500
    return False


class JsonPlaceholderClient(Client):
    def __init__(self) -> None:
        super().__init__(
            ClientSession(base_url="https://jsonplaceholder.typicode.com", raise_for_status=True)
        )

    @endpoint("/todos", retry(on=should_retry, stop=after_attempt(3), wait=fixed(5) + jit(2)))
    async def get_todos(self, user_id: Annotated[int, api_ref("userId")] = None) -> list[Todo]:
        ...

    @endpoint("/users/{user_id}/todos")
    async def get_todos_by_user(self, user_id: int) -> list[Todo]:
        ...

    @endpoint("/todos")
    async def post_todo(self, todo: Annotated[Todo, api_ref("body")]) -> Todo:
        ...


@pytest.mark.asyncio()
async def test_todos_filter_by_user() -> None:
    # WHEN
    async with JsonPlaceholderClient() as client:
        todos = await client.get_todos(user_id=1)

    # THEN
    assert all(todo.user_id == 1 for todo in todos)


@pytest.mark.asyncio()
async def test_todos_get_by_user() -> None:
    # WHEN
    async with JsonPlaceholderClient() as client:
        todos = await client.get_todos_by_user(1)

    # THEN
    assert len(todos) == 20


@pytest.mark.asyncio()
async def test_post_todo() -> None:
    # GIVEN
    new_todo = Todo.model_construct(user_id=1, id=201, title="test post todo", completed=False)

    # WHEN
    async with JsonPlaceholderClient() as client:
        created_todo = await client.post_todo(new_todo)

    # THEN
    assert created_todo == new_todo
