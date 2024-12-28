## Return Types

Methods marked with the `@endpoint` decorator can declare one of the following return types:

- `bytes`
- `str`
- `dict` or `TypedDict`
- a dataclass
- a Pydantic model
- a container type of any type mentioned above
- `meatie.AsyncResponse` or `meatie.Response` - wrapper for a response returned by the underlying HTTP client library

Using dataclasses, `TypedDict` or `Pydantic` models require the `Pydantic` library to be installed.

## Rename HTTP Query Parameters

Parameters that are not part of the URL path are sent as query parameters if their value is not `None`. By default, the
name of the query parameter is derived
from the name used in the method signature. Use the `api_ref` function to send the query parameter with a different
name.

```python
from typing import Annotated

from aiohttp import ClientSession
from meatie import api_ref, endpoint
from meatie_aiohttp import Client


class JsonPlaceholderClient(Client):
    def __init__(self) -> None:
        super().__init__(ClientSession(base_url="https://jsonplaceholder.typicode.com"))

    @endpoint("/todos")
    async def get_todos(self, user_id: Annotated[int, api_ref("userId")] = None) -> list[dict]:
        ...
```

## Query Parameter Serialization

```python
from typing import Annotated

from aiohttp import ClientSession
from meatie import endpoint, api_ref
from meatie_aiohttp import Client


class Params:
    @staticmethod
    def bool(value: bool) -> str:
        return str(value).lower()


class JsonPlaceholderClient(Client):
    def __init__(self) -> None:
        super().__init__(ClientSession(base_url="https://jsonplaceholder.typicode.com"))

    @endpoint("/users/{user_id}/todos")
    async def get_todos_by_user(self, user_id: int, completed: Annotated[bool, api_ref(fmt=Params.bool)]) -> list[dict]:
        ...

```

## Send Multiple Query Parameters for a Single Method Argument

```python
from dataclasses import dataclass
from typing import Annotated, Any, Self

from aiohttp import ClientSession
from meatie import api_ref, endpoint
from meatie_aiohttp import Client
from pydantic import BaseModel, Field


class Todo(BaseModel):
    user_id: int = Field(alias="userId")
    id: int
    title: str
    completed: bool


@dataclass
class TodoParams:
    user_id: int | None = None
    completed: bool | None = None

    @classmethod
    def unwrap(cls, value: Self) -> dict[str, Any]:
        values = {}

        if value.user_id is not None:
            values["userId"] = value.user_id

        if value.completed is not None:
            values["completed"] = str(value.completed).lower()

        return values


class JsonPlaceholderClient(Client):
    def __init__(self) -> None:
        super().__init__(ClientSession(base_url="https://jsonplaceholder.typicode.com"))

    @endpoint("/todos")
    async def get_todos(
            self, params: Annotated[TodoParams, api_ref(unwrap=TodoParams.unwrap)] = None
    ) -> list[Todo]:
        ...
```

## Send Multiple Query Parameters with the Same Name

```python
from typing import Annotated

from aiohttp import ClientSession
from meatie import api_ref, endpoint
from meatie_aiohttp import Client


class JsonPlaceholderClient(Client):
    def __init__(self) -> None:
        super().__init__(ClientSession(base_url="https://jsonplaceholder.typicode.com"))

    @endpoint("/todos")
    async def get_todos(self, user_ids: Annotated[list[int], api_ref("userId")] = None) -> list[dict]:
        ...

```

## Custom Request Body Serialization

```python
from typing import Any, Annotated

from aiohttp import ClientSession
from meatie import endpoint, api_ref
from meatie_aiohttp import Client
from pydantic import BaseModel, Field


class Todo(BaseModel):
    user_id: int = Field(alias="userId")
    id: int
    title: str
    completed: bool


class Params:
    @staticmethod
    def todo(value: Todo) -> dict[str, Any]:
        return value.model_dump(by_alias=True)


class JsonPlaceholderClient(Client):
    def __init__(self) -> None:
        super().__init__(ClientSession(base_url="https://jsonplaceholder.typicode.com"))

    @endpoint("/todos")
    async def post_todo(self, todo: Annotated[Todo, api_ref("body", fmt=Params.todo)]) -> Todo:
        ...
```

## Control Response Body Deserialization

```python
from typing import Annotated, Any

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

```

## Error Handling

```python
from typing import Annotated

from aiohttp import ClientSession
from meatie import AsyncResponse, HttpStatusError, api_ref, body, endpoint
from meatie_aiohttp import Client


async def get_error(response: AsyncResponse) -> Exception | None:
    if 200 <= response.status < 300:
        return None

    return HttpStatusError(response)


class JsonPlaceholderClient(Client):
    def __init__(self) -> None:
        super().__init__(ClientSession(base_url="https://jsonplaceholder.typicode.com"))

    @endpoint("/todos", body(error=get_error))
    async def get_todos(self, user_id: Annotated[int, api_ref("userId")] = None) -> list[dict]:
        ...
```

## Define the HTTP Method

Meatie infers the HTTP method from the method name defined in Python. Use the `method` argument to override the default
behavior.

```python
from typing import Annotated

from aiohttp import ClientSession
from meatie import api_ref, endpoint
from meatie_aiohttp import Client


class JsonPlaceholderClient(Client):
    def __init__(self) -> None:
        super().__init__(ClientSession(base_url="https://jsonplaceholder.typicode.com"))

    @endpoint("/todos", method="GET")
    async def list_todos(self, user_id: Annotated[int, api_ref("userId")] = None) -> list[dict]:
        ...
```

