#  Copyright 2023 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
from typing import Annotated

import httpx
import pytest
from meatie import api_ref, endpoint
from meatie_httpx import AsyncClient, Client
from pydantic import BaseModel, Field


class Todo(BaseModel):
    user_id: int = Field(alias="userId")
    id: int
    title: str
    completed: bool


class JsonPlaceholderClient(Client):
    def __init__(self) -> None:
        super().__init__(httpx.Client(base_url="https://jsonplaceholder.typicode.com"))

    @endpoint("/todos")
    def get_todos(self, user_id: Annotated[int, api_ref("userId")] = None) -> list[Todo]:
        ...

    @endpoint("/users/{user_id}/todos")
    def get_todos_by_user(self, user_id: int) -> list[Todo]:
        ...

    @endpoint("/todos")
    def post_todo(self, todo: Annotated[Todo, api_ref("body")]) -> Todo:
        ...


class JsonPlaceholderAsyncClient(AsyncClient):
    def __init__(self) -> None:
        super().__init__(httpx.AsyncClient(base_url="https://jsonplaceholder.typicode.com"))

    @endpoint("/todos")
    async def get_todos(self, user_id: Annotated[int, api_ref("userId")] = None) -> list[Todo]:
        ...

    @endpoint("/users/{user_id}/todos")
    async def get_todos_by_user(self, user_id: int) -> list[Todo]:
        ...

    @endpoint("/todos")
    async def post_todo(self, todo: Annotated[Todo, api_ref("body")]) -> Todo:
        ...


def test_todos_filter_by_user() -> None:
    # WHEN
    with JsonPlaceholderClient() as client:
        todos = client.get_todos(user_id=1)

    # THEN
    assert all(todo.user_id == 1 for todo in todos)


def test_todos_get_by_user() -> None:
    # WHEN
    with JsonPlaceholderClient() as client:
        todos = client.get_todos_by_user(1)

    # THEN
    assert len(todos) == 20


def test_post_todo() -> None:
    # GIVEN
    new_todo = Todo.model_construct(user_id=1, id=201, title="test post todo", completed=False)

    # WHEN
    with JsonPlaceholderClient() as client:
        created_todo = client.post_todo(new_todo)

    # THEN
    assert created_todo == new_todo


@pytest.mark.asyncio()
async def test_todos_filter_by_user_async() -> None:
    # WHEN
    async with JsonPlaceholderAsyncClient() as client:
        todos = await client.get_todos(user_id=1)

    # THEN
    assert all(todo.user_id == 1 for todo in todos)


@pytest.mark.asyncio()
async def test_todos_get_by_user_async() -> None:
    # WHEN
    async with JsonPlaceholderAsyncClient() as client:
        todos = await client.get_todos_by_user(1)

    # THEN
    assert len(todos) == 20


@pytest.mark.asyncio()
async def test_post_todo_async() -> None:
    # GIVEN
    new_todo = Todo.model_construct(user_id=1, id=201, title="test post todo", completed=False)

    # WHEN
    async with JsonPlaceholderAsyncClient() as client:
        created_todo = await client.post_todo(new_todo)

    # THEN
    assert created_todo == new_todo
