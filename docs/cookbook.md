# Cookbook

The cookbook provides solutions to the most frequently asked questions by the community.

The first section briefly describes how the `@endpoint` descriptor works. The remaining sections present practical
recipes for customizing Meatie behavior when dealing with HTTP query parameters, request/response body serialization,
and error handling.

# Table of Contents

1. [Endpoint Descriptor](#endpoint-descriptor)
2. [Query Parameters](#query-parameters)
3. [JSON Serialization](#json-serialization)
4. [Error Handling](#error-handling)

## Endpoint Descriptor

Meatie generates code for calling REST APIs for method signatures marked with the `@endpoint`
descriptor. See [descriptors](https://docs.python.org/3/howto/descriptor.html) for more information about this Python
metaprogramming feature.

There are a few requirements regarding the application of the `@endpoint` descriptor.

The descriptor is available in a class that inherits from the abstract class [
`meatie.BaseClient`](../src/meatie/client.py) or [`meatie.BaseAsyncClient`](../src/meatie/aio/client.py). Meatie
provides implementations of these abstract classes for the
most popular HTTP libraries: [`meatie_httpx.Client`](../src/meatie_httpx/client.py), [
`meatie_requests.Client`](../src/meatie_requests/client.py), and [
`meatie_aiohttp.Client`](../src/meatie_aiohttp/client.py).

The methods should be empty. Meatie won't call the method code directly. Leaving any implementation besides a docstring
is a deadcode.

The remaining sections focus on method names, input arguments, and return types.

### Method Name

It is common to prefix the method with the HTTP method name (i.e., `get_`, `post_`, etc.). Meatie will use the prefix to
determine the desired HTTP method. However, this naming convention is optional, and you can use any naming scheme that
suits your project. If you don't use HTTP methods as a prefix, define the desired HTTP method in the `@endpoint`
descriptor.

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

### Method Arguments

Method arguments referenced in the URL path are required. Other arguments are optional and are sent as HTTP query
parameters only if their values are not equal to `None`. Customization of HTTP query parameters deserves a separate
section [Query Parameters](#query-parameters) to discuss it in sufficient detail.

### Return Type

Methods can return different Python types. Supporting it may require Meatie to process the response body. The table
below contains supported return types and actions taken by Meatie.

| Return Type                                 | Action on the HTTP response body |
|---------------------------------------------|----------------------------------|
| `None`                                      | No action                        |
| `bytes`                                     | Read to bytes                    |
| `str`                                       | Read and decode to text          |
| `dict`                                      | Parse using JSON decoder         |
| `TypedDict`                                 | Parse using Pydantic             |
| dataclass                                   | Parse using Pydantic             |
| Pydantic model                              | Parse using Pydantic             |
| Container type of any type mentioned above  | Parse using Pydantic             |
| `meatie.AsyncResponse` or `meatie.Response` | No action                        |

## Query Parameters

Processing of query parameters is customizable through the `api_ref` function.

### Renaming Parameters

By default, the query parameter name is the same as the argument name used in the method signature. Use the `api_ref`
function to change the default value.

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

### Serialization

Use the `api_ref` function to pass the serialization function. The function should return `str` or `bytes`.

The example below shows how to send a query parameter as a string `true` or `false`.

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

### Sending Multiple Parameters with the Same Name

Declare the query parameter as a list and use the `api_ref` function to customize query parameter handling if needed.
The serialization function should return a list of `str` or 'bytes`.

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

### Sending Multiple Parameters for a Single Input Argument

Suppose you want to send multiple HTTP query parameters derived from an input argument. It is a common pattern to deal
with endpoints that support large number of input parameters or endpoints with parameters that have complex
dependencies.
Then, instead of defining a function with large number of arguments, one could define a new data type that represents
all input arguments of the endpoint.

Use the `api_ref` function and pass a function that accepts the input model and returns a dictionary of query
parameters.

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

## JSON Serialization

The section demonstrates how to control JSON serialization of HTTP requests and deserialization of HTTP responses.

### Request Body Serialization

Pass the serialization function using the `fmt` parameter of the `api_ref` function. If the function returns either
`str` or `bytes`, then the result is sent directly to the external API. Conversely, if you return a `dict`, then the
HTTP client library will perform JSON serialization.

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

### Response Body Deserialization

Pass the deserialization function using the `json` parameter of the `body` function.

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

Some REST APIs report errors using a data model that doesn't meet the schema requirements of a successful response. To
interact with such APIs, we suggest providing Meatie with a callback function that inspects the HTTP response before
parsing its body using the Pydantic model. If the callback returns an exception, Meatie will abort processing the
response and raise the exception. Then, depending on the error type, the operation could be retried after some delay, or
aborted by raising the exception again to the application.

Pass the callback that should check response errors using the `json` parameter of the `body` function.

```python
from typing import Annotated

from aiohttp import ClientSession
from meatie import AsyncResponse, HttpStatusError, api_ref, body, endpoint, ResponseError
from meatie_aiohttp import Client
from pydantic import BaseModel, Field


class Todo(BaseModel):
    user_id: int = Field(alias="userId")
    id: int
    title: str
    completed: bool


class ApiError(ResponseError):

    def __init__(self, response: AsyncResponse, error_code: str, error_msg: str) -> None:
        super(self).__init__(response)
        self.error_code = error_code
        self.error_msg = error_msg


async def get_error(response: AsyncResponse) -> Exception | None:
    json = await response.json()
    error_code = json.get("error_code")
    if error_code is not None:
        error_msg = json.get("error_msg")
        return ApiError(response, error_code, error_msg)

    if 200 <= response.status < 300:
        return None

    return HttpStatusError(response)


class JsonPlaceholderClient(Client):
    def __init__(self) -> None:
        super().__init__(ClientSession(base_url="https://jsonplaceholder.typicode.com", raise_for_status=True))

    @endpoint("/todos", body(error=get_error))
    async def get_todos(self, user_id: Annotated[int, api_ref("userId")] = None) -> list[dict]:
        ...
```
