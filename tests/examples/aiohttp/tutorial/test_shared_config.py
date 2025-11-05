#  Copyright 2025 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
from typing import Annotated, TypeVar, override
from typing_extensions import ParamSpec, Callable, Any

import pytest
from aiohttp import ClientSession
from pydantic import BaseModel, Field

from meatie import (
    Limiter,
    Rate,
    RetryContext,
    Method,
    api_ref,
    endpoint,
    limit,
    private,
    MINUTE,
    Request,
    HttpStatusError,
    after_attempt,
    cache,
    fixed,
    jit,
    retry,
)
from meatie_aiohttp import Client


def should_retry(ctx: RetryContext) -> bool:
    if isinstance(ctx.error, HttpStatusError):
        return ctx.error.response.status >= 500
    return False


class Todo(BaseModel):
    user_id: int = Field(alias="userId")
    id: int
    title: str
    completed: bool


class JsonPlaceholderClient(Client):
    def __init__(self) -> None:
        super().__init__(
            ClientSession(base_url="https://jsonplaceholder.typicode.com"),
            limiter=Limiter(Rate(tokens_per_sec=10), capacity=10),
        )

    @endpoint(
        "/todos",
        limit(tokens=1),
        private,
        retry(on=should_retry, stop=after_attempt(3), wait=fixed(5) + jit(2)),
        cache(ttl=MINUTE),
    )
    async def get_todos(self, user_id: Annotated[int, api_ref("userId")] = None) -> list[Todo]: ...

    @endpoint(
        "/users/{user_id}/todos",
        limit(tokens=1),
        private,
        retry(on=should_retry, stop=after_attempt(3), wait=fixed(5) + jit(2)),
        cache(ttl=MINUTE),
    )
    async def get_user_todos(self, user_id: int) -> list[Todo]: ...

    @override
    async def authenticate(self, request: Request) -> None:
        request.headers["Authorization"] = "Bearer bWVhdGll"


PT = ParamSpec("PT")
T = TypeVar("T")


def my_endpoint(path: str, *args: Any, method: Method | None = None) -> Callable[[Callable[PT, T]], Callable[PT, T]]:
    return endpoint(
        path,
        limit(tokens=1),
        private,
        retry(on=should_retry, stop=after_attempt(3), wait=fixed(5) + jit(2)),
        cache(ttl=MINUTE),
        method=method,
    )


class JsonPlaceholderClientV2(Client):
    def __init__(self) -> None:
        super().__init__(
            ClientSession(base_url="https://jsonplaceholder.typicode.com"),
            limiter=Limiter(Rate(tokens_per_sec=10), capacity=10),
        )

    @my_endpoint("/todos")
    async def get_todos(self, user_id: Annotated[int, api_ref("userId")] = None) -> list[Todo]: ...

    @my_endpoint("/users/{user_id}/todos")
    async def get_user_todos(self, user_id: int) -> list[Todo]: ...

    @override
    async def authenticate(self, request: Request) -> None:
        request.headers["Authorization"] = "Bearer bWVhdGll"


@pytest.mark.asyncio()
async def test_todos_filter_by_user() -> None:
    # WHEN
    async with JsonPlaceholderClientV2() as client:
        todos = await client.get_todos(user_id=1)

    # THEN
    assert all(todo.user_id == 1 for todo in todos)
