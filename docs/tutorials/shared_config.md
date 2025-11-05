This post demonstrates a pattern for sharing configuration settings across multiple endpoints of a meatie client to avoid repetition.

Suppose you are implementing an HTTP client for an API. Ideally, every endpoint of the API uses the same approach for error reporting and retries. Furthermore, it is common for all public endpoints to use a similar cache configuration.

Let's consider the following code example. All endpoints are private and share the same retry policy, rate-limiting, and cache settings. Repeating this configuration for each endpoint definition leads to duplication.

```py hl_lines="51-54 60-63"
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
        private,
        limit(tokens=1),
        retry(on=should_retry, stop=after_attempt(3), wait=fixed(5) + jit(2)),
        cache(ttl=MINUTE),
    )
    async def get_todos(self, user_id: Annotated[int, api_ref("userId")] = None) -> list[Todo]: ...

    @endpoint(
        "/users/{user_id}/todos",
        private,
        limit(tokens=1),
        retry(on=should_retry, stop=after_attempt(3), wait=fixed(5) + jit(2)),
        cache(ttl=MINUTE),
    )
    async def get_user_todos(self, user_id: int) -> list[Todo]: ...

    @override
    async def authenticate(self, request: Request) -> None:
        request.headers["Authorization"] = "Bearer bWVhdGll"

```

A pragmatic way to deal with this duplication is to extract the common settings into a variable and reference it in the endpoint definitions, as the example below demonstrates.

```py hl_lines="3 12 15"
(...) # imports are skipped for brevity

_cfg = (limit(tokens=1), private, retry(on=should_retry, stop=after_attempt(3), wait=fixed(5) + jit(2)), cache(ttl=MINUTE))

class JsonPlaceholderClient(Client):
    def __init__(self) -> None:
        super().__init__(
            ClientSession(base_url="https://jsonplaceholder.typicode.com"),
            limiter=Limiter(Rate(tokens_per_sec=10), capacity=10),
        )

    @endpoint("/todos", *_cfg)
    async def get_todos(self, user_id: Annotated[int, api_ref("userId")] = None) -> list[Todo]: ...

    @endpoint("/users/{user_id}/todos", *_cfg)
    async def get_user_todos(self, user_id: int) -> list[Todo]: ...

    @override
    async def authenticate(self, request: Request) -> None:
        request.headers["Authorization"] = "Bearer bWVhdGll"

```

You can improve the code further by defining a custom `endpoint` decorator through composition.

```py hl_lines="3-11 21 24"
(...) # imports are skipped for brevity

def my_endpoint(path: str, *args: Any, method: Method | None = None) -> Callable[[Callable[PT, T]], Callable[PT, T]]:
    return endpoint(
        path,
        limit(tokens=1),
        private,
        retry(on=should_retry, stop=after_attempt(3), wait=fixed(5) + jit(2)),
        cache(ttl=MINUTE),
        method=method,
    )


class JsonPlaceholderClient(Client):
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

```

Feel free to use whichever approach you prefer, or a combination of them. The result is reduced duplication and a more readable client definition.

This example concludes the tutorial series on Meatie's core features. If you spot an error or have a suggestion for improvement, we appreciate your feedback :pray: Pull requests are especially welcome, as they help us address suggestions faster.
