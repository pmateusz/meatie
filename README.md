<img src="https://repository-images.githubusercontent.com/735134836/df6752b8-38fa-4550-968e-cd2eda4adb37" alt="meatie">

[![GitHub Test Badge][1]][2] [![codecov.io][3]][4] [![pypi.org][5]][6] [![versions][7]][8]
[![downloads][9]][10] [![License][11]][12]

[1]: https://github.com/pmateusz/meatie/actions/workflows/ci.yaml/badge.svg "GitHub CI Badge"

[2]: https://github.com/pmateusz/meatie/actions/workflows/ci.yaml "GitHub Actions Page"

[3]: https://codecov.io/gh/pmateusz/meatie/branch/master/graph/badge.svg?branch=master "Coverage Badge"

[4]: https://codecov.io/gh/pmateusz/meatie?branch=master "Codecov site"

[5]: https://img.shields.io/pypi/v/meatie.svg "Pypi Latest Version Badge"

[6]: https://pypi.python.org/pypi/meatie "Pypi site"

[7]:https://img.shields.io/pypi/pyversions/meatie.svg

[8]: https://github.com/pmateusz/meatie

[9]: https://static.pepy.tech/badge/meatie

[10]: https://pepy.tech/project/meatie

[11]: https://img.shields.io/github/license/pmateusz/meatie "License Badge"

[12]: https://opensource.org/license/bsd-3-clause "License"

Meatie is a Python library that simplifies the implementation of REST API clients. The library generates code for
calling REST endpoints based on method signatures annotated with type hints. Meatie takes care of mechanics related to
HTTP communication, such as building URLs, encoding query parameters, and serializing the body in the HTTP requests and
responses. Rate limiting, retries, and caching are available with some modest extra setup.

Meatie works with all major HTTP client libraries (request, httpx, aiohttp) and offers seamless integration with
Pydantic (v1 and v2). The minimum officially supported version is Python 3.9.

## TL;DR

Generate HTTP clients using type annotations.

```python
from typing import Annotated

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
    async def get_todos(self, user_id: Annotated[int, api_ref("userId")] = None) -> list[Todo]: ...

    @endpoint("/users/{user_id}/todos")
    async def get_todos_by_user(self, user_id: int) -> list[Todo]: ...

    @endpoint("/todos")
    async def post_todo(self, todo: Annotated[Todo, api_ref("body")]) -> Todo: ...
```

Do you use a different HTTP client library in your project? See the example adapted for [
`requests`](./tests/examples/requests/tutorial/test_basics.py) and [
`httpx`](./tests/examples/httpx/tutorial/test_basics.py).

### Caching

Cache result for a given TTL.

```python
from typing import Annotated

from meatie import MINUTE, api_ref, cache, endpoint
from meatie_aiohttp import Client
from pydantic import BaseModel


class Todo(BaseModel):
    ...


class JsonPlaceholderClient(Client):
    ...

    @endpoint("/todos", cache(ttl=MINUTE, shared=False))
    async def get_todos(self, user_id: Annotated[int, api_ref("userId")] = None) -> list[Todo]:
        ...
```

A cache key is built based on the URL path and query parameters. It does not include the scheme or the network location.
By default, every HTTP client instance has an independent cache. The behavior can be changed in the endpoint definition
to share cached results across all HTTP client class instances.

### Rate Limiting

Meatie can delay HTTP requests that exceed the predefined rate limit.

```python
from typing import Annotated

from aiohttp import ClientSession
from meatie import Limiter, Rate, api_ref, endpoint, limit
from meatie_aiohttp import Client
from pydantic import BaseModel


class Todo(BaseModel):
    ...


class JsonPlaceholderClient(Client):
    def __init__(self) -> None:
        super().__init__(
            ClientSession(base_url="https://jsonplaceholder.typicode.com"),
            limiter=Limiter(Rate(tokens_per_sec=10), capacity=10),
        )

    @endpoint("/todos", limit(tokens=2))
    async def get_todos(self, user_id: Annotated[int, api_ref("userId")] = None) -> list[Todo]:
        ...
```

### Retries

Meatie can retry failed HTTP requests following the strategy set in the endpoint definition. The retry strategy is
controlled using third-party functions that specify when a retry should be attempted, how long to wait between
consecutive attempts to call the endpoint, and whether to abort further retries.

```python
from typing import Annotated

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
from pydantic import BaseModel


class Todo(BaseModel):
    ...


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
```

Meatie comes with a built-in set of predefined functions for building retry strategies. See
the [meatie.retry](./src/meatie/option/retry_option.py) option for more details.

### Calling Private Endpoints

Meatie can inject additional information into the HTTP request. A typical example is adding the `Authorization` header
with a token or signing the request using API keys.

```python
from typing import Annotated, override

from aiohttp import ClientSession
from meatie import Request, api_ref, endpoint, private
from meatie_aiohttp import Client
from pydantic import BaseModel


class Todo(BaseModel):
    ...


class JsonPlaceholderClient(Client):
    def __init__(self) -> None:
        super().__init__(ClientSession(base_url="https://jsonplaceholder.typicode.com"))

    @endpoint("/todos", private)
    async def get_todos(self, user_id: Annotated[int, api_ref("userId")] = None) -> list[Todo]:
        ...

    @override
    async def authenticate(self, request: Request) -> None:
        request.headers["Authorization"] = "Bearer bWVhdGll"
```

## More Examples

Need more control over processing the HTTP requests or responses? See the [Meatie Cookbook](./docs/cookbook.md) with
solutions to the most frequently asked questions by the community.
